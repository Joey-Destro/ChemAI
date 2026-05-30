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
    {'name': 'Name'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{Image}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{Name}}',
    },
  ])

PATHWAY_MODEL = genanki.Model(
  1607392320,
  'Pathway Occlusion Model',
  fields=[
    {'name': 'OccludedImage'},
    {'name': 'MasterImage'},
    {'name': 'RevealedName'},
  ],
  templates=[
    {
      'name': 'Card 1',
      'qfmt': '{{OccludedImage}}',
      'afmt': '{{FrontSide}}<hr id="answer">{{MasterImage}}<br><br><b>{{RevealedName}}</b>',
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
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

    text_content = extract_text(file_path)

    prompt = f"""
    Extract a list of all chemical compounds and molecules from the following text.
    For each compound, provide its standard chemical name and its corresponding SMILES string.
    Return ONLY a valid JSON array of objects, where each object has 'name' and 'smiles' keys.
    Do not include markdown blocks or any other text.

    Text:
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
        name = comp.get('name')
        smiles = comp.get('smiles')

        if not smiles or not name:
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
            fields=[f'<img src="{img_filename}">', name]
        )
        deck.add_note(note)

    package.media_files = media_files
    package.write_to_file(output_deck_path)

    return output_deck_path

def create_pathway_deck(file_path: str, api_key: str, output_deck_path: str) -> str:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

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

    # Render Graphviz and get layout data
    tmp_dir = tempfile.mkdtemp()
    master_svg_path = os.path.join(tmp_dir, "master") # Graphviz adds extension

    dot = graphviz.Digraph(format='svg')
    dot.attr(rankdir='TB')

    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    for node in nodes:
        dot.node(node['id'], node['label'])
    for edge in edges:
        dot.edge(edge['source'], edge['target'], label=edge.get('label', ''))

    # Render to SVG (SVG contains bounding box info)
    dot.render(master_svg_path)

    # Render to PNG for Anki
    dot.format = 'png'
    master_png_path = dot.render(master_svg_path + "_png")

    # We will use the layout output format 'json' from graphviz to get exact coordinates
    dot.format = 'json'
    json_path = dot.render(master_svg_path + "_layout")

    with open(json_path, 'r') as f:
        layout_data = json.load(f)

    # Open the rendered master PNG to get its dimensions and to draw on
    master_img = Image.open(master_png_path).convert('RGB')

    deck_id = 2059400111
    deck = genanki.Deck(deck_id, 'Biochemistry Pathways')
    package = genanki.Package(deck)

    media_files = [master_png_path]
    master_filename = os.path.basename(master_png_path)

    # Parse graphviz JSON layout
    # Graphviz json output gives nodes in 'objects' array
    objects = layout_data.get('objects', [])

    # Graphviz outputs coordinates in points (72 points per inch).
    # The PNG output resolution (DPI) determines pixel coordinates. Default Graphviz DPI is usually 96.
    # The JSON format gives bb (bounding box) as "llx,lly,urx,ury" in points.

    # To properly map coordinates, we extract bounding boxes
    # Often, drawing black boxes directly over the nodes requires translating these coordinates
    # We will approximate by drawing over the center and dimensions provided in 'pos' and 'width'/'height'

    for obj in objects:
        if 'name' not in obj or 'label' not in obj:
            continue

        node_name = obj['name']
        node_label = obj['label']

        # Nodes don't have 'bb', they have 'pos' (center "x,y"), 'width' (inches), and 'height' (inches)
        pos_str = obj.get('pos', "")
        if not pos_str:
            continue

        pos_coords = [float(x) for x in pos_str.split(',')]
        cx_pt, cy_pt = pos_coords

        # width and height are in inches, need to convert to points (*72)
        width_pt = float(obj.get('width', 0)) * 72.0
        height_pt = float(obj.get('height', 0)) * 72.0

        llx = cx_pt - (width_pt / 2.0)
        urx = cx_pt + (width_pt / 2.0)
        lly = cy_pt - (height_pt / 2.0)
        ury = cy_pt + (height_pt / 2.0)

        # In Graphviz points, y grows upwards. In Pillow pixels, y grows downwards.
        # Graphviz JSON output usually gives a 'bb' for the whole graph to know total height.
        graph_bb = layout_data['bb'].split(',')
        graph_height_pt = float(graph_bb[3])

        # Translate to pixel coordinates assuming 96 DPI (96 pixels per 72 points = 4/3 multiplier)
        dpi_mult = 96.0 / 72.0

        # Invert Y axis
        pixel_lly = (graph_height_pt - ury) * dpi_mult
        pixel_ury = (graph_height_pt - lly) * dpi_mult
        pixel_llx = llx * dpi_mult
        pixel_urx = urx * dpi_mult

        # Expand box slightly to cover text fully
        pad = 5
        box = [pixel_llx - pad, pixel_lly - pad, pixel_urx + pad, pixel_ury + pad]

        # Create occluded image
        occluded_img = master_img.copy()
        draw = ImageDraw.Draw(occluded_img)
        draw.rectangle(box, fill="black")

        occluded_filename = f"{uuid.uuid4().hex}_occluded.png"
        occluded_path = os.path.join(tmp_dir, occluded_filename)
        occluded_img.save(occluded_path)

        media_files.append(occluded_path)

        note = genanki.Note(
            model=PATHWAY_MODEL,
            fields=[
                f'<img src="{occluded_filename}">',
                f'<img src="{master_filename}">',
                node_label
            ]
        )
        deck.add_note(note)

    package.media_files = media_files
    package.write_to_file(output_deck_path)

    return output_deck_path
