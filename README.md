# FMC-Inventory
Python script to output inventory of managed devices in Cisco Firepower Management Center (FMC)

this script will will generate an output file FTD-device-list.csv containing the appliance inventory managed by FMC
FMC misreports the serial number of the appliances.  to obtain the serial associated with support contracts it will be queried
directly from the cli of the appliance and extracted using regular expression. this technique currently only works on FTD
appliances, not ASA running FTD code
