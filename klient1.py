from socket import *

serverNavn = "export.eduhost.dk"
serverPort = 60141
dataSocket = socket(AF_INET, SOCK_DGRAM)

cpr = input("Indtast cpr-nr: ")

with open("konfigurationsfil.xml", "r") as f:
    konfigurationsfil_indhold = f.readlines()

for linje in konfigurationsfil_indhold:

    dele = linje.strip().split(',')

    behandlingsstedid, adgangskode = dele[2],dele[3]

    data = f"<Hent><cpr>{cpr}</cpr><behandlingsstedid>{behandlingsstedid}</behandlingsstedid><adgangskode>{adgangskode}</adgangskode></Hent>"
    print("Sender til server:", data)
    dataSocket.sendto(data.encode(), (serverNavn, serverPort))

    svar, afsender = dataSocket.recvfrom(2048)
    print("Server:", svar.decode())

dataSocket.close()