# SocketLlama
Just playing around with abdeladim-s/pyllamacpp

This is a super basic terminal interface, you might want [pyllamacpp-webui](https://github.com/abdeladim-s/pyllamacpp#web-ui)

## Setup & Run

```
git clone https://github.com/Aveygo/LlamaSocket.git
cd LlamaSocket
pip3 install pyllamacpp
curl -o ggml-alpaca-7b-q4.bin -C - https://gateway.estuary.tech/gw/ipfs/QmQ1bf2BTnYxq73MFJWu1B7bQ2UD6qG7D7YDCxhTndVkPC
python3 main.py
```

## Client
```
telnet localhost 8080
```

or

```
nc localhost 8080
```
