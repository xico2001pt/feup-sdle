# SDLE 2022/2023 - Assignment #2: Decentralized Timeline

## Description

Implementation of a centralized timeline service (e.g. Twitter, Instagram, Facebook) that harvests peer-to-peer devices for the SDLE curricular unit using [Kademlia](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf), [ZMQ](https://zeromq.org/) and [Django](https://www.djangoproject.com/) technologies.

## How to run

Make sure the `make` utility is installed, as well as the necessary python libraries by executing `pip install -r src/requirements.txt` command from the project root directory (assuming python and pip are installed).

From the project’s root:
- Start 5 instances of Django servers and Kademlia nodes by executing the `make run` command;
- Optionally, for debugging purposes, open one instance of a Django server and Kademlia node through the `make bootstrap` command;
- Each Django server will be served in ports 8000 through 8004 (including), open them through any up-to-date browser (e.g. url=`localhost:8000`);
- When done experimenting, execute the `make stop` and `make clean` commands.

---

## Group T04G13

- Adriano Soares (up201904873@edu.fe.up.pt)
- António Ribeiro (up201906761@edu.fe.up.pt)
- Filipe Campos (up201905609@edu.fe.up.pt)
- Francisco Cerqueira (up201905337@edu.fe.up.pt)