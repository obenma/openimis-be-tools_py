from defusedxml.ElementTree import parse


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def sanitize_xml(xml_file):
    return parse(xml_file)


def dmy_format_sql(vendor, field_name):
    if vendor == "postgresql":
        return """TO_CHAR({},'DD-MM-YYYY')""".format(field_name)
    else:
        return """CONVERT(NVARCHAR(10),{},103)""".format(field_name)
