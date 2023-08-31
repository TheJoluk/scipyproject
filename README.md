
## Motivation
The Motivation is to create a simple console based chat service with python3. 
The Chat Client saves all send messages of all users with the corresponding ip address to run statistics about the usage and messages.

## Goal
The Goal is to create a Chat Client and Server with Python3. The Chat Services should be able to be able to deal with multiple users.
The User can set up Username, ServerIP and ServerPort on startup to decide to which server he wants to connect with which username.
During the chat process all chat messages are getting stored in a pandas dataframe to run statistics on them. 
As an example the statics of messages per minute is getting printed on request.

## Structure
The project contains two files, the server and the client.
The server file provides the backbone of the chat service which takes all the messages send and broadcast them to all the other currently connect clients.
Furthermore, the server tracks the message history of all clients.

The client file provides an easy use to connect to the server and to set the username of the user. 
Beside that the client offers the possibility to request a list of all currently connected users.

## Requirements
The Chat Service only runs on Linux based operating system due to limitation on the unblocking reading of commandline inputs on windows.
That means on windows the python script is not running.
Beside the Linux requirement the project needs following python libraries available. <br>
•  socket <br>
•  sys <br> 
•  struct <br>
•  signal <br>
•  time <br>
•  select <br> 
•  pandas  <br>
•  numpy <br>
•  matplotlib.pyplot  <br>
All libraries are either default packages or easy to install with pip install


## Setup
The IP Address, Port and Username is requested on startup of the Client. Therefore, beside the previous mentioned requirements nothing more needs to be cared about.

## Usage
Run the server script on the local machine or on a server which is exposed to the internet. After that run the client script(s) to connect to the server.
After entering IP, Port and username you are free to chat with everyone involved.

To run the scripts use:
*python3 chat_server.py*
*python3 chat_client.py*

Due to limited resources you most likely want to run it on "localhost" to be able to test it on a single machine. 
You can still execute the chat client in multiple instances.

For additional functionalities you can type /help into the client to get a list on all available commands with an explanation.
Similar to that you can type "help" without slash into the server program to list all available commands with an explanation.

## Future Improvements

This project can be extended in the future by adding additional commands. Some example would be to change nickname while running the client, change to server ip on the fly 
or change color in which certain users are display. 
Beside that the available statistics on the server side can be enhanced by analysing the language used, 
track the location of users or just by tracking the currently connected users additional to  send messages.
This project provides a good foundation for adding additional functionality.
