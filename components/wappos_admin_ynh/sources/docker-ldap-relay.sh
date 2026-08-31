#!/bin/bash
set -eu
exec socat TCP-LISTEN:1389,bind=0.0.0.0,fork,reuseaddr,range=172.16.0.0/12 TCP:127.0.0.1:389
