import openpyxl

wb = openpyxl.load_workbook('templates/DATA/Sensor_Data_Full/VC27634_ChestCompression.xlsx', read_only=True)
sheet = wb.active
rows = sheet.iter_rows(values_only=True)

for i, row in enumerate(rows):
    if i < 10:
        print(row)
    else:
        break
