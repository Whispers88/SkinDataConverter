# Skin Data Converter

The **Skin Data Converter** is a Python-based tool that converts imported skins JSON files from **SkinBox**, **XSkinMenu (XSkins)**, **Skin Controller**, and **LSkins** into the format required by **Skinner**.

It outputs a JSON map where each key is a **workshop/skin ID (ulong)**:

```json
{
  "3578172696": {},
  "3578171093": {}
}
```

---

## Supported Input Files

You can import one or multiple JSON files from:

- **SkinBox**  
  `config/skinbox.json`

- **XSkinMenu (XSkins)**  
  `data/XDataSystem/XSkinMenu/Skins.json`

- **Skin Controller**  
  `data/SkinController/Workshopskins.json`

- **LSkins**  
  Any of the JSON files in data/LSkins/Skins.... for example box.wooden.large.json

---

## How To Use (Windows EXE)

1. Run `Skin Data Converter.exe`
2. Add your JSON file(s) by either:
   - Clicking **Add…** and selecting one or more JSON files, **or**
   - Dragging and dropping multiple `.json` files onto the app window
3. Copy the output into:  
   `oxide/data/skinner/ImportedSkins.json`

> Tip: You can keep adding files — IDs will keep accumulating until you press **Clear**.

---

## Notes

- Duplicate skins are ignored automatically
- Only valid numeric IDs are included (as unsigned 64-bit values)
- Use **Clear** to reset the file list and start over

---

## Running From Source (Optional)

If you’re running the script instead of the EXE:

### Requirements

- Python 3.10+ recommended

### Install dependencies

```bash
pip install sv-ttk tkinterdnd2
```

### Run

```bash
python main.py
```

- `sv-ttk` provides the modern dark theme
- `tkinterdnd2` enables drag & drop (the tool still works without it, but drag & drop will be disabled)

---

## Output Destination (Skinner)

Paste or save the converted output into:

`oxide/data/skinner/ImportedSkins.json`
