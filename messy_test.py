def clean_and_simple():
    print("I am a good function.")
    return True

def terrible_messy_function(data_list):
    # This function has too many nested loops and conditions!
    count = 0
    if data_list:
        for item in data_list:
            if item > 10:
                print("Too big")
            elif item < 0:
                print("Too small")
            else:
                for i in range(item):
                    if i % 2 == 0:
                        count += 1
                    elif i % 3 == 0:
                        count -= 1
    return count