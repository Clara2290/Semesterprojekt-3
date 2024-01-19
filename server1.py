from socket import *
from DBAccess import *
import xml.etree.ElementTree as ET

serverPort = 60141
dataSocket = socket(AF_INET, SOCK_DGRAM)

conn = dbaccess()
cursor = conn.cursor()

dataSocket.bind(("", serverPort))
print("Server klar til at modtage")

while True:
    data, afsender = dataSocket.recvfrom(2048)
    try:
        root = ET.fromstring(data.decode())
        cpr = root.find("cpr").text
        print(cpr)
        behandlingsstedid = root.find("behandlingsstedid").text
        print(behandlingsstedid)
        adgangskode = root.find("adgangskode").text
        print(adgangskode)
    except ET.ParseError:
        print("Fejl i XML-format. Kan ikke fortsætte.")
        continue

    query_validate = f"SELECT * FROM behandlingssted WHERE behandlingsstedid='{behandlingsstedid}' AND adgangskode='{adgangskode}'"
    cursor.execute(query_validate)
    print("SQL Query(validate);", query_validate)
    validate_result = cursor.fetchone()

    if validate_result:
        cpr_query = f"""
            SELECT patient.cpr, indkaldelse.tidspunkt, behandlingssted.navn AS behandlingssted_navn, afdeling.navn AS afdeling_navn
            FROM indkaldelse
            JOIN patient ON indkaldelse.patientid = patient.patientid
            JOIN afdeling ON indkaldelse.afdelingid = afdeling.afdelingid
            JOIN behandlingssted ON afdeling.behandlingsstedid = behandlingssted.behandlingsstedid
            WHERE patient.cpr = '{cpr}';
        """

        cursor.execute(cpr_query)
        print("SQL Query(validate);", cpr_query)
        cpr_result = cursor.fetchone()

        if cpr_result:
            cpr, tidspunkt, behandlingssted, afdeling = cpr_result
            svar = f"Validering successful. cpr:{cpr}, Tidspunkt:{tidspunkt}, Behandlingssted:{behandlingssted}, Afdeling:{afdeling}"
        else:
            svar = "Du har ingen kommende behandlinger"

        # Omdan svar til et XML-format
        response_root = ET.Element("Response")
        response_element = ET.SubElement(response_root, "Result")
        response_element.text = svar
        xml_response = ET.tostring(response_root, encoding="utf-8").decode("utf-8")

    else:
        svar = "Ugyldig adgangskode eller behandlingssted"

    print(afsender, ":", behandlingsstedid, adgangskode, "->", svar)
    dataSocket.sendto(xml_response.encode(), afsender)

conn.commit()
conn.close()




