import os
import json
import uuid
import tempfile
import google.generativeai as genai
import genanki
from rdkit import Chem
from rdkit.Chem import Draw
import graphviz
from PIL import Image, ImageDraw
import PyPDF2

# Configure genanki models
COMPOUND_MODEL = genanki.Model(
  1607392319,
  'Standard Compound Model',
  fields=[
    {'name': 'Image'},
    {'name': 'TrivialName'},
    {'name': 'IupacName'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Image}}',
      'afmt': '{{FrontSide}}<hr id="answer"><b>{{TrivialName}}</b><br><span style="color:gray; font-size:14px;">{{IupacName}}</span>',
    },
  ])

# Use a template that mimics Anki's Image Occlusion Enhanced note type
IO_MODEL = genanki.Model(
  1607392320,
  'Image Occlusion Enhanced',
  fields=[
    {'name': 'Image'},
    {'name': 'Question Mask'},
    {'name': 'Answer Mask'},
    {'name': 'Original Image'},
    {'name': 'Header'},
    {'name': 'Footer'},
    {'name': 'Remarks'},
  ],
  templates=[
    {
      'name': 'Image Occlusion Enhanced',
      'qfmt': '''
        <div id="io-header">{{Header}}</div>
        <div id="io-wrapper" style="position:relative; display:inline-block;">
            <div id="io-image">{{Image}}</div>
            <div id="io-overlay" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">
                {{Question Mask}}
            </div>
        </div>
        <div id="io-footer">{{Footer}}</div>
      ''',
      'afmt': '''
        <div id="io-header">{{Header}}</div>
        <div id="io-wrapper" style="position:relative; display:inline-block;">
            <div id="io-image">{{Image}}</div>
            <div id="io-overlay" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none;">
                {{Answer Mask}}
            </div>
        </div>
        <div id="io-footer">{{Footer}}</div>
        <hr>
        <div id="io-remarks">{{Remarks}}</div>
      ''',
    },
  ])

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF file."""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text(file_path: str) -> str:
    if file_path.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def create_standard_compounds_deck(file_path: str, api_key: str, output_deck_path: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')

    text_content = extract_text(file_path)

    prompt = f"""
    Jsi přísný zkoušející z lékařské biochemie. Tvým úkolem je ze zadaného seznamu látek vygenerovat ABSOLUTNĚ VYČERPÁVAJÍCÍ sadu.

    Tvá striktní pravidla pro generování, která nesmíš porušit:

    1. ZÁKAZ SHRNUTÍ A ZKRACOVÁNÍ: Nesmíš vynechat jedinou látku. Musíš projít dokument řádek po řádku. Z každé jednotlivé látky zmíněné v textu musí vzniknout samostatný objekt.

    2. ROZBALENÍ SKUPIN A DRAH (KRITICKÉ): Pokud dokument zmiňuje metabolickou dráhu (např. "citrátový cyklus", "glykolýza", "močovinový cyklus") nebo skupinu látek (např. "20 proteinogenních aminokyselin", "monokarboxylové kyseliny po C5", "základní alifatické uhlovodíky do C10"), tvým úkolem je tyto skupiny DEKÓDOVAT. Vygeneruješ samostatný objekt pro KAŽDÝ JEDEN meziprodukt a KAŽDOU JEDNU konkrétní molekulu, která do dané dráhy nebo skupiny patří.

    3. DVOJÍ NÁZVOSLOVÍ: Každý vygenerovaný objekt musí obsahovat jak běžně užívaný triviální název, tak přesný systematický název (IUPAC), pokud existuje.

    4. JAZYK: Veškerý výstup, popisy a názvosloví musí být v bezchybné češtině.

    5. STRUKTURA (SMILES): Pro každou sloučeninu musíš dodat její platný chemický řetězec SMILES, ze kterého se vygeneruje 2D struktura.

    VYŽADOVANÝ VÝSTUP:
    Vrať POUZE validní JSON pole objektů. Každý objekt musí mít PŘESNĚ tyto tři klíče:
    - "trivial_name" (Triviální název v češtině)
    - "iupac_name" (Systémový IUPAC název v češtině)
    - "smiles" (Platný SMILES kód)
    Nevypisuj žádný markdown, žádný úvodní ani závěrečný text.

    Text k analýze:
    {text_content[:30000]} # Limit to avoid token overflow
    """

    response = model.generate_content(prompt)
    try:
        # Strip potential markdown formatting
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        compounds = json.loads(response_text)
    except Exception as e:
        raise Exception(f"Failed to parse Gemini response as JSON: {response.text}")

    # Initialize Anki Deck
    deck_id = 2059400110
    deck = genanki.Deck(deck_id, 'Biochemistry Compounds')
    package = genanki.Package(deck)

    media_files = []
    tmp_dir = tempfile.mkdtemp()

    for comp in compounds:
        trivial_name = comp.get('trivial_name')
        iupac_name = comp.get('iupac_name')
        smiles = comp.get('smiles')

        if not smiles or not trivial_name:
            continue

        # Generate RDKit image
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue # Skip invalid SMILES

        img_filename = f"{uuid.uuid4().hex}.png"
        img_path = os.path.join(tmp_dir, img_filename)

        Draw.MolToFile(mol, img_path, size=(300, 300))
        media_files.append(img_path)

        # Add to deck
        note = genanki.Note(
            model=COMPOUND_MODEL,
            fields=[f'<img src="{img_filename}">', trivial_name, iupac_name or ""]
        )
        deck.add_note(note)

    package.media_files = media_files
    package.write_to_file(output_deck_path)

    return output_deck_path

def create_pathway_deck(file_path: str, api_key: str, output_deck_path: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.5-flash')

    text_content = extract_text(file_path)

    prompt = f"""
    Analyze the following text and identify metabolic pathways (like glycolysis, citric acid cycle, etc.).
    Extract the main pathway as a directed graph.
    Return ONLY a valid JSON object representing the graph. The JSON MUST follow this exact structure:
    {{
        "nodes": [
            {{"id": "n1", "label": "Glucose"}},
            {{"id": "n2", "label": "Glucose-6-phosphate"}}
        ],
        "edges": [
            {{"source": "n1", "target": "n2", "label": "Hexokinase"}}
        ]
    }}
    Do not include markdown blocks or any other text.

    Text:
    {text_content[:30000]}
    """

    response = model.generate_content(prompt)
    try:
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        graph_data = json.loads(response_text)
    except Exception as e:
        raise Exception(f"Failed to parse Gemini response as JSON: {response.text}")

    tmp_dir = tempfile.mkdtemp()
    master_svg_path = os.path.join(tmp_dir, "master")

    dot = graphviz.Digraph(format='svg')
    dot.attr(rankdir='TB')

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    for node in nodes:
        dot.node(node['id'], node['label'])
    for edge in edges:
        dot.edge(edge['source'], edge['target'], label=edge.get('label', ''))

    dot.render(master_svg_path)

    # Render to PNG for Anki
    dot.format = 'png'
    master_png_path = dot.render(master_svg_path + "_png")

    # Use JSON layout to get coordinates
    dot.format = 'json'
    json_path = dot.render(master_svg_path + "_layout")

    with open(json_path, 'r') as f:
        layout_data = json.load(f)

    master_img = Image.open(master_png_path)
    img_width, img_height = master_img.size

    deck_id = 2059400111
    deck = genanki.Deck(deck_id, 'Biochemistry Pathways')
    package = genanki.Package(deck)

    media_files = [master_png_path]
    master_filename = os.path.basename(master_png_path)

    # Parse graphviz JSON layout
    objects = layout_data.get('objects', [])

    all_rects = []
    node_data = []

    for obj in objects:
        if 'name' not in obj or 'label' not in obj:
            continue

        pos_str = obj.get('pos', "")
        if not pos_str:
            continue

        pos_coords = [float(x) for x in pos_str.split(',')]
        cx_pt, cy_pt = pos_coords

        width_pt = float(obj.get('width', 0)) * 72.0
        height_pt = float(obj.get('height', 0)) * 72.0

        llx = cx_pt - (width_pt / 2.0)
        urx = cx_pt + (width_pt / 2.0)
        lly = cy_pt - (height_pt / 2.0)
        ury = cy_pt + (height_pt / 2.0)

        graph_bb = layout_data['bb'].split(',')
        graph_height_pt = float(graph_bb[3])

        dpi_mult = 96.0 / 72.0

        pixel_lly = (graph_height_pt - ury) * dpi_mult
        pixel_ury = (graph_height_pt - lly) * dpi_mult
        pixel_llx = llx * dpi_mult
        pixel_urx = urx * dpi_mult

        pad = 5
        x = pixel_llx - pad
        y = pixel_lly - pad
        w = (pixel_urx - pixel_llx) + (pad * 2)
        h = (pixel_ury - pixel_lly) + (pad * 2)

        rect_svg = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFE3A8" stroke="#333" stroke-width="1"></rect>'

        node_data.append({
            'label': obj['label'],
            'rect': rect_svg
        })
        all_rects.append(rect_svg)

    # Now create a "Hide All, Guess One" style note for each node
    for target_node in node_data:
        # Question mask shows ALL boxes
        q_mask = f'<svg width="{img_width}" height="{img_height}" viewBox="0 0 {img_width} {img_height}">'
        for rect in all_rects:
            if rect == target_node['rect']:
                # The target shape is styled differently to stand out
                q_mask += rect.replace('fill="#FFE3A8"', 'fill="#FF5252"')
            else:
                q_mask += rect
        q_mask += '</svg>'

        # Answer mask hides all EXCEPT the target box (which is transparent/omitted)
        a_mask = f'<svg width="{img_width}" height="{img_height}" viewBox="0 0 {img_width} {img_height}">'
        for rect in all_rects:
            if rect != target_node['rect']:
                a_mask += rect
        a_mask += '</svg>'

        note = genanki.Note(
            model=IO_MODEL,
            fields=[
                f'<img src="{master_filename}">',
                q_mask,
                a_mask,
                f'<img src="{master_filename}">',
                'Metabolic Pathway',
                '',
                target_node['label']
            ]
        )
        deck.add_note(note)

    package.media_files = media_files
    package.write_to_file(output_deck_path)

    return output_deck_path
