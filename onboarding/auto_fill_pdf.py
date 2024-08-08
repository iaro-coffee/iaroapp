from fillpdf import fillpdfs

form_fields_dict = fillpdfs.get_form_fields("test.pdf")
form_fields = list(fillpdfs.get_form_fields("test.pdf").keys())

for field_name, field_value in form_fields_dict.items():
    if isinstance(field_value, list):
        print(f"{field_name}: {', '.join(map(str, field_value))}")
    else:
        print(f"{field_name}: {field_value}")

first_name = "Alex"
last_name = "Appleseed"
address = "Rosenstrasse 11"
bio = "testing multifields"

data_dict = {
    form_fields[0]: first_name,
    form_fields[1]: last_name,
    form_fields[2]: address,
    form_fields[3]: bio,
    form_fields[5]: "Value_rpug",
    form_fields[6]: "Yes_sbkl",
    form_fields[7]: None,
}

fillpdfs.write_fillable_pdf("test.pdf", "filled.pdf", data_dict)
