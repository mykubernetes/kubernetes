#!/bin/bash

openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout mooc.key -out mooc.crt -subj "/CN=*.mooc.com/O=*.mooc.com"

kubectl create secret tls mooc-tls --key mooc.key --cert mooc.crt
