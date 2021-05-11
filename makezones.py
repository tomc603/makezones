#!/usr/bin/env python3

import argparse
import csv
import ipaddress
import json
import random
import string

TLDS = ["com.", "net.", "org.", "co.uk."]


def randomLabel():
    output = ""
    for i in range(random.randint(1,63)):
        # The first character of a label must be a letter
        if len(output) == 0:
            output = random.choice(string.ascii_lowercase)
            continue
        output += random.choice(string.ascii_lowercase + string.digits + "-")
    return output


def rrHeader(rrName, rrType, rrClass, rrTTL):
    return {
        "Name": rrName,
        "Rrtype": rrType,
        "Class": rrClass,
        "TTL": rrTTL,
        "Rdlength": 0
    }


def aRecord(rrLabel, rrTTL):
    return {
        "Hdr": rrHeader(rrName=rrLabel, rrType=1, rrClass=1, rrTTL=rrTTL),
        "A": str(ipaddress.ip_address(random.randbytes(4)))
    }


def aaaaRecord(rrLabel, rrTTL):
    return {
        "Hdr": rrHeader(rrName=rrLabel, rrType=28, rrClass=1, rrTTL=rrTTL),
        "AAAA": str(ipaddress.ip_address(random.randbytes(4)))
    }


def cnameRecord(rrLabel, rrTTL):
    return {
        "Hdr": rrHeader(rrName=rrLabel, rrType=5, rrClass=1, rrTTL=rrTTL),
        "Target": '.'.join([randomLabel(), randomLabel(), random.choice(TLDS)])
    }


def mxRecord(rrLabel, rrTTL):
    name = '.'.join([randomLabel(), randomLabel(), random.choice(TLDS)])
    return {
        "Hdr": rrHeader(rrName=rrLabel, rrType=15, rrClass=1, rrTTL=rrTTL),
        "Preference": 10 * random.randint(1,5),
        "Mx": name
    }


def randomRecord(recordLabel, recordType, recordTTL):
    for rrCount in range(random.randint(1, 5)):
        rr = {}
        if recordType == 1:
            rr = aRecord(recordLabel, recordTTL)
        elif recordType == 5:
            rr = cnameRecord(recordLabel, recordTTL)
        elif recordType == 15:
            rr = mxRecord(recordLabel, recordTTL)
        elif recordType == 28:
            rr = aaaaRecord(recordLabel, recordTTL)
    return rr


def randomRecords(zoneLabel):
    recordEntry = {}

    for labelCount in range(random.randint(1, 5)):
        # Always create records for the zone itself, then add records for extra zones
        recordLabel = zoneLabel
        if labelCount > 1:
            recordLabel = randomLabel() + '.' + zoneLabel

        recordEntry[recordLabel] = {}
        for recordType in [1, 5, 15, 28]:
            # Randomly decide if we should populate this record type
            if random.choice([True, False]):
                if recordType == 15 and recordLabel != zoneLabel:
                    # Don't create MX records for anthing but the origin
                    continue

                if recordType == 5 and recordLabel == zoneLabel:
                    # Skip creation of CNAME for the origin
                    continue

                recordTTL = random.randint(60, 7*24*60*60)
                recordEntry[recordLabel][recordType] = []

                # Add a random number of records for the record type
                for rrCount in range(random.randint(1, 5)):
                    rr = randomRecord(recordLabel, recordType, recordTTL)
                    recordEntry[recordLabel][recordType].append(rr)

                if recordType == 5:
                    # If we created a CNAME, delete any A records and skip creating any others.
                    recordEntry[recordLabel].pop(1, None)
                    break
    return recordEntry


def main():
    parser = argparse.ArgumentParser(prog='make-zone', description='Create random DNS zone data for a collection of domains.')
    parser.add_argument('-i', '--input', dest='input', type=str, required=True, help='CSV file containing a list of domains.')
    parser.add_argument('-o', '--output', dest='output', type=str, required=True, help='JSON file for results.')
    args = parser.parse_args()

    random.seed()
    data = {}
    print("Creating zone data...")
    with open(args.input, 'r') as f:
        values = csv.reader(f)
        for value in values:
            zoneLabel = value[1]
            records = randomRecords(zoneLabel)
            expire = random.randint(240, 4294967295)

            soa = {
                "Hdr": {
                    "Name": zoneLabel + ".",
                    "Rrtype": 6,
                    "Class": 1,
                    "TTL": 212,
                    "Rdlength": 0
                },
                "Ns": "ns-{:02}.blackjackdns.net.".format(random.randint(1, 8)),
                "Mbox": "hostmaster.blackjackdns.net.",
                "Serial": random.randint(1, 4294967295),
                "Refresh": int(expire / 2),
                "Retry": int(expire / 4),
                "Expire": expire,
                "Minttl": 60
            }

            data[zoneLabel] = {
                "SOA": soa,
                "Records": records
            }

    print("Writing results...")
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)


if __name__ == '__main__':
    main()

