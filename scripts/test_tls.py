"""Prove installed QuickFIX sends FIX Logon over mutually authenticated TLS.

Only loopback and ephemeral test certificates are used. This is not a
Bloomberg connectivity test or a certification of hostname validation.
"""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import queue
import socket
import ssl
import threading
import traceback

import quickfix as fix
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


def make_certificate(folder):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=1))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
            .add_extension(x509.ExtendedKeyUsage([
                ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)
            .sign(key, hashes.SHA256()))
    cert_path = folder / 'test-cert.pem'
    key_path = folder / 'test-key.pem'
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    return cert_path, key_path


def message(kind, sequence, extra=''):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H:%M:%S')
    body = (f'35={kind}|49=SERVER|56=CLIENT|34={sequence}|52={stamp}|' + extra)
    body = body.replace('|', '\x01').encode('ascii')
    raw = b'8=FIX.4.4\x019=' + str(len(body)).encode() + b'\x01' + body
    return raw + f'10={sum(raw) % 256:03d}\x01'.encode()


class Application(fix.Application):
    def __init__(self):
        super().__init__()
        self.logged_on = threading.Event()

    def onCreate(self, session): pass
    def onLogon(self, session): self.logged_on.set()
    def onLogout(self, session): pass
    def toAdmin(self, message, session): pass
    def fromAdmin(self, message, session): pass
    def toApp(self, message, session): pass
    def fromApp(self, message, session): pass


def main():
    out = Path('smoke-output').resolve()
    out.mkdir(exist_ok=True)
    cert, key = make_certificate(out)
    results = queue.Queue()
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(1)
    listener.settimeout(25)
    port = listener.getsockname()[1]

    def server():
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(str(cert), str(key))
            context.load_verify_locations(cafile=str(cert))
            context.verify_mode = ssl.CERT_REQUIRED
            with listener:
                conn, _ = listener.accept()
                conn.settimeout(20)
                with context.wrap_socket(conn, server_side=True) as secure:
                    assert secure.getpeercert(), 'Client certificate missing'
                    raw = b''
                    while b'\x0110=' not in raw or not raw.endswith(b'\x01'):
                        chunk = secure.recv(4096)
                        if not chunk:
                            raise AssertionError('Disconnected before FIX Logon')
                        raw += chunk
                        if len(raw) > 65536:
                            raise AssertionError('Unexpectedly large message')
                    assert b'\x0135=A\x01' in raw, raw
                    secure.sendall(message('A', 1, '98=0|108=30|'))
                    results.put({'tls_version': secure.version(),
                                 'client_certificate_verified': True,
                                 'fix_logon_received': True})
                    # Keep the transport open until QuickFIX performs logout.
                    while True:
                        raw = secure.recv(4096)
                        if not raw:
                            break
                        if b'35=5\x01' in raw:
                            secure.sendall(message('5', 2))
                            break
        except Exception:
            results.put({'error': traceback.format_exc()})

    thread = threading.Thread(target=server, daemon=True)
    thread.start()
    cfg = out / 'session.cfg'
    cfg.write_text(f'''[DEFAULT]
ConnectionType=initiator
ReconnectInterval=2
StartTime=00:00:00
EndTime=00:00:00
HeartBtInt=30
UseDataDictionary=N
ResetOnLogon=Y
SSLProtocol=TLSv1_2
ClientCertificateFile={cert.as_posix()}
ClientCertificateKeyFile={key.as_posix()}
CertificationAuthoritiesFile={cert.as_posix()}
FileLogPath={out.as_posix()}/logs

[SESSION]
BeginString=FIX.4.4
SenderCompID=CLIENT
TargetCompID=SERVER
SocketConnectHost=127.0.0.1
SocketConnectPort={port}
''', encoding='ascii')
    settings = fix.SessionSettings(str(cfg))
    app = Application()
    store = fix.MemoryStoreFactory()
    log = fix.FileLogFactory(settings)
    initiator = fix.SSLSocketInitiator(app, store, settings, log)
    try:
        initiator.start()
        success = app.logged_on.wait(25)
        result = results.get(timeout=2)
        if 'error' in result:
            raise AssertionError(result['error'])
        assert success, 'QuickFIX did not reach onLogon'
        result['quickfix_on_logon'] = True
        result['module'] = fix.__file__
        (out / 'tls-result.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
    finally:
        initiator.stop()
        thread.join(timeout=5)
        cert.unlink(missing_ok=True)
        key.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
