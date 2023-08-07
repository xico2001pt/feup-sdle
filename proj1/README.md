# SDLE 2022/2023 - Assignment #1: Reliable Pub/Sub Service

[**Report link**](docs/report.pdf)

---

## Description

Implementation of a publish-subscription service for the SDLE curricular unit using the [ZMQ](https://zeromq.org/) library.

## How to run

Make sure the [PyZMQ](https://github.com/zeromq/pyzmq) library package is installed. This can be achieved by executing the command `pip install pyzmq` in the command line (assuming Python is installed).

From the project’s root:
- Start the server process: `python3 src/server.py`
- Run the client command line interface: `python3 src/cli.py client_directory`

The *client_dir* may already exist as a result of a previous execution, in that case, all the information it contains will be used in the current session. Else, a new directory is created.

In the client command line interface, type the following operations after the “Enter command” prompt accordingly:
- `GET <topic>`
- `PUT <topic> <publication>`
- `SUB <topic>`
- `UNSUB <topic>`
- `EXIT`

---

## Group T04G13

- Adriano Soares (up201904873@edu.fe.up.pt)
- António Ribeiro (up201906761@edu.fe.up.pt)
- Filipe Campos (up201905609@edu.fe.up.pt)
- Francisco Cerqueira (up201905337@edu.fe.up.pt)