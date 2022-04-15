#!/bin/bash
sesearch -A -s isolated_app policy > isolated_app.te
sesearch -A -s untrusted_app policy > untrusted_app.te
sesearch -A -s priv_app policy > priv_app.te
sesearch -A -s platform_app policy > platform_app.te
sesearch -A -s system_app policy > system_app.te
sesearch -A -s system_server policy > system_server.te
sesearch -A -s radio policy > radio.te