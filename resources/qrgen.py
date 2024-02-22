import websockets
import asyncio
import aiohttp
import ujson
import qrcode
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Cipher import PKCS1_OAEP
import base64


class QR:
    def __init__(self):
        self.key = RSA.generate(2048)
        self.cipher = PKCS1_OAEP.new(self.key, hashAlgo=SHA256)

    def decrypt_payload(self, encrypted_payload):
        payload = base64.b64decode(encrypted_payload)
        decrypted = self.cipher.decrypt(payload)

        return decrypted

    async def create_qr(self, name):
        fingerprint = await self.generate_fingerprint()
        img = qrcode.make(f"https://discordapp.com/ra/{fingerprint}")
        img.save(f"./resources/codes/qr-code-{name}.png")

    async def wait_token(self):
        try:
            while True:
                item = await asyncio.wait_for(self.recv_json(), timeout=60)
                print(f"Received item: {item}")  # Print the received item
                if item["op"] == "pending_login":
                    token = await self.decrypt_ticket(item["ticket"])
                    print(f"Decrypted token: {token}")  # Print the decrypted token
                    return token
        except asyncio.TimeoutError:
            print("Timeout while waiting for token.")


    async def decrypt_ticket(self, ticket):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://discord.com/api/v9/users/@me/remote-auth/login",
                headers={
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.115 Safari/537.36"
                },
                json={"ticket": ticket},
            ) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    payload = j["encrypted_token"]
                    token = self.decrypt_payload(payload)
                    return token.decode("utf-8")

    async def tokeninfo(self, _token, embed):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://discord.com/api/v9/users/@me",
                headers={
                    "authorization": _token,
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.135 Chrome/91.0.4472.164 Electron/13.6.6 Safari/537.36",
                },
            ) as resp:
                if resp.status == 200:
                    j = await resp.json()
                    for key, value in j.items():
                        embed.add_embed_field(
                            name=f"`{key}`", value=f"{value}", inline=False
                        )

    async def send_json(self, payload: dict):
        await self.ws.send(ujson.dumps(payload))

    async def recv_json(self):
        item = await self.ws.recv()
        return ujson.loads(item)

    async def connect_ws(self):
        self.ws = await websockets.connect(
            "wss://remote-auth-gateway.discord.gg/?v=2", origin="https://discord.com"
        )

    async def heartbeat(self, interval):
        while True:
            await asyncio.sleep(interval)
            payload = {"op": "heartbeat"}
            await self.send_json(payload)

    def generate_pubkey(self):
        pub_key = self.key.publickey().export_key().decode("utf-8")
        pub_key = "".join(pub_key.split("\n")[1:-1])
        return pub_key

    async def generate_fingerprint(self):
        await self.connect_ws()

        item = await self.recv_json()
        if item["op"] == "hello":
            interval = item["heartbeat_interval"]
        pubkey = self.generate_pubkey()
        await self.send_json({"op": "init", "encoded_public_key": pubkey})
        asyncio.create_task(self.heartbeat(interval))
        item = await self.recv_json()
        if item["op"] == "nonce_proof":
            nonce = item["encrypted_nonce"]
            decrypted = self.decrypt_payload(nonce)
            proof = SHA256.new(data=decrypted).digest()
            proof = base64.urlsafe_b64encode(proof)
            proof = proof.decode().rstrip("=")
            await self.send_json({"op": "nonce_proof", "proof": proof})

            item = await self.recv_json()
            return item["fingerprint"]
