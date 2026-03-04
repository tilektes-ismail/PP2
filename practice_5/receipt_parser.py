import re, json


def parse_check() -> list:
    with open("raw.txt", "r", encoding = "UTF-8") as f:
        txt = f.read()
    result = {}

    product_info = re.findall(r"^\d+\.\n(.+)\n(.+)\n(.+)", txt, re.MULTILINE)
    # product_ids = re.findall(r"^\d+\.$", txt, re.M)
    # parsed_product_ids = [int(i[0:-1]) for i in product_ids]
    # max_id = max(i for i in parsed_product_ids)

    # max_len = 1
    # for product in product_info:
    #     # print(product[0], "lenth: ", len(product[0]))
    #     if len(product[0]) > max_len:
    #         max_len = len(product[0])

    # print(max_len)

    print("Check info")
    print("=" * 145)
    print(f"{"id":5} {"Product Name: ":100} {"Product Price":10}")
    print("-" * 145)
    id = 1
    result = []
    for product in product_info:
        product_name = product[0]
        product_unit_price_info = product[1]
        product_quantity = (product_unit_price_info.split(" x "))[0]
        product_unit_price = (product_unit_price_info.split(" x "))[1]
        product_price = product[2]
        print(f"{id}.    {product_name:100} {product_price:10}")
        product_dict_info = {
            "product_id": id,
            "product_name": product_name,
            "product_unitprice": product_unit_price,
            "product_quantity": product_quantity,
            "total_price": product_price
        }
        result.append(product_dict_info)
        id += 1

    print("-" * 145)
    total_amount = re.findall(r"^ИТОГО:\n(.+)", txt, re.M)

    payment_method = re.findall(r"^(.*)\n(.+)\nИТОГО", txt, re.M)
    date = re.findall(r"^Время: (.+)", txt, re.M)
    final_payment_method = payment_method[0][0][0:-1]
    result.append(f"payment_method: {final_payment_method}")
    print(f"Payment method: {final_payment_method}")
    result.append(f"check_date: {date[0]}")
    print(f"Date: {date[0]}")
    result.append(f"Total: {total_amount[0]}")
    print(f"Total: {total_amount[0]}")
    return result

a = parse_check()
# parsed_data = json.dumps(a, separators = (",", ":"))
# print("\n", *a, sep = "\n")
# print("\n", parsed_data)