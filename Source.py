import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

def convert_json(data):
    new_data = {"Imported Skins List": {}}
    if isinstance(data, dict):
        if "Imported Workshop Skins" in data:
            for key, values in data["Imported Workshop Skins"].items():
                for value in values:
                    new_data["Imported Skins List"][str(value)] = {}
            return new_data
        else:
            if "Skins" in data: #Umod Skins
                for value in data["Skins"]:
                    for skin in value["Skins"]:
                        new_data["Imported Skins List"][str(skin)] = {}
                return new_data
            else:
                for key, values in data.items():
                    for value in values:
                        ["Imported Skins List"][str(value)] = {}
            return new_data
        
    elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
        for item in data:
            if "SkinID" in item:
                new_data["Imported Skins List"][item["SkinID"]] = {}
        return new_data
    else:
        output_text.insert(tk.END, "Unsupported JSON structure")
        raise ValueError("Unsupported JSON structure")
    
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, 'r') as file:
            data = json.load(file)
            converted_data = convert_json(data)
            display_output(converted_data)

def display_output(data):
    json_str = json.dumps(data, indent=4)
    lines = json_str.split('\n')
    if len(lines) > 2:
        lines = lines[1:-1]  # Remove the first and last lines
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, '\n'.join(lines))

def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(output_text.get(1.0, tk.END))

root = tk.Tk()
root.title("Skin Data Converter")

select_button = tk.Button(root, text="Select JSON Data File", command=select_file)
select_button.pack(pady=10)

output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
output_text.pack(pady=10)

copy_button = tk.Button(root, text="Copy to Clipboard", command=copy_to_clipboard)
copy_button.pack(pady=10)

root.mainloop()
