# -*- coding: utf-8 -*-
"""
docx_helpers.py — Constructor de documentos .docx sobre una plantilla.

Un .docx es un ZIP con XML adentro. Este módulo:
  1. Abre la plantilla Gnombres_Dat252.docx como ZIP
  2. Reemplaza word/document.xml por el que armamos aquí
  3. Agrega las imágenes en word/media/ y las registra en las relaciones
  4. Deja intactos styles.xml, theme1.xml, settings.xml y el sectPr
"""

from __future__ import annotations
import io, pathlib, re, shutil, zipfile, struct

EMU_POR_CM = 360000
EMU_POR_PULGADA = 914400

# XML namespaces
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
TIPO_IMAGEN = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"

def esc(t):
    """Escape text for XML."""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def run(texto, negrita=False, cursiva=False, sz=None, color="000000", mono=False, sub=False, sup=False):
    """A text run with formatting. sz is in half-points (24 = 12pt)."""
    rpr = []
    if negrita: rpr.append("<w:b/>")
    if cursiva: rpr.append("<w:i/>")
    if mono: rpr.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>')
    if sz: rpr.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    rpr.append(f'<w:color w:val="{color}"/>')
    if sub: rpr.append('<w:vertAlign w:val="subscript"/>')
    if sup: rpr.append('<w:vertAlign w:val="superscript"/>')
    rpr.append('<w:lang w:val="es-BO"/>')
    return f'<w:r><w:rPr>{"".join(rpr)}</w:rPr><w:t xml:space="preserve">{esc(texto)}</w:t></w:r>'

# Mini-markup parser: **bold** __italic__ `mono` ~sub~ ^sup^
_MARCAS = re.compile(r"(\*\*.+?\*\*|__.+?__|`[^`]+?`|~[^~]+?~|\^[^\^]+?\^|\n)")

def runs_con_marcas(texto, sz=None, color="000000"):
    """Convert mini-markup to XML runs."""
    out = []
    last_end = 0
    for m in _MARCAS.finditer(texto):
        if m.start() > last_end:
            out.append(run(texto[last_end:m.start()], sz=sz, color=color))
        
        token = m.group(1)
        if token == '\n':
            out.append('<w:r><w:br/></w:r>')
        elif token.startswith('**'):
            out.append(run(token[2:-2], negrita=True, sz=sz, color=color))
        elif token.startswith('__'):
            out.append(run(token[2:-2], cursiva=True, sz=sz, color=color))
        elif token.startswith('`'):
            out.append(run(token[1:-1], mono=True, sz=sz, color=color))
        elif token.startswith('~'):
            out.append(run(token[1:-1], sub=True, sz=sz, color=color))
        elif token.startswith('^'):
            out.append(run(token[1:-1], sup=True, sz=sz, color=color))
            
        last_end = m.end()
        
    if last_end < len(texto):
        out.append(run(texto[last_end:], sz=sz, color=color))
        
    return "".join(out)

def parrafo(contenido_runs, jc=None, antes=0, despues=200, linea=276, borde_inf=None, sangria=0, mantener=False):
    """A paragraph. contenido_runs is already XML."""
    ppr = []
    if jc:
        ppr.append(f'<w:jc w:val="{jc}"/>')
    ppr.append(f'<w:spacing w:before="{antes}" w:after="{despues}" w:line="{linea}" w:lineRule="auto"/>')
    if sangria:
        ppr.append(f'<w:ind w:left="{sangria}"/>')
    if mantener:
        ppr.append('<w:keepNext/><w:keepLines/>')
    if borde_inf:
        ppr.append(f'<w:pBdr><w:bottom w:val="single" w:sz="{borde_inf}" w:space="1" w:color="auto"/></w:pBdr>')
        
    ppr_xml = f'<w:pPr>{"".join(ppr)}</w:pPr>' if ppr else ""
    return f'<w:p>{ppr_xml}{contenido_runs}</w:p>'

def salto_pagina():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

def _tamano_png(datos):
    """Width and height in pixels from PNG IHDR header."""
    if datos[:8] != b'\x89PNG\r\n\x1a\n':
        return 800, 600
    w, h = struct.unpack(">LL", datos[16:24])
    return w, h

class Documento:
    """Accumulates XML body and images, rewrites the ZIP at the end."""
    def __init__(self, plantilla):
        self.plantilla = pathlib.Path(plantilla)
        self.body_xml = []
        self.imagenes = [] # tuples of (id, path, datos)
        self.img_counter = 1
        
        self.sect_pr = '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1417" w:right="1701" w:bottom="1417" w:left="1701" w:header="708" w:footer="708" w:gutter="0"/></w:sectPr>'
        if self.plantilla.exists():
            try:
                with zipfile.ZipFile(self.plantilla, 'r') as zin:
                    if 'word/document.xml' in zin.namelist():
                        doc_xml = zin.read('word/document.xml').decode('utf-8')
                        m = re.search(r'(<w:sectPr.*?</w:sectPr>)', doc_xml)
                        if m:
                            self.sect_pr = m.group(1)
            except zipfile.BadZipFile:
                pass

    def add(self, xml):
        self.body_xml.append(xml)

    def titulo_seccion(self, texto):
        self.add(parrafo(runs_con_marcas(texto, sz=28), jc="left", antes=240, despues=120, mantener=True, borde_inf=4))

    def titulo_sub(self, texto):
        self.add(parrafo(runs_con_marcas(texto, sz=24), jc="left", antes=200, despues=80, mantener=True))

    def texto(self, contenido, jc="both", sz=22, despues=160, sangria=0):
        self.add(parrafo(runs_con_marcas(contenido, sz=sz), jc=jc, despues=despues, sangria=sangria))

    def vinieta(self, contenido, sz=22):
        r = f'<w:r><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/><w:sz w:val="{sz}"/></w:rPr><w:t></w:t></w:r><w:r><w:tab/></w:r>'
        self.add(parrafo(r + runs_con_marcas(contenido, sz=sz), sangria=720, antes=40, despues=40))

    def espacio(self, alto=120):
        self.add(parrafo("", despues=alto))

    def regla(self, color="000000", grosor=4, antes=0, despues=120):
        self.add(parrafo("", antes=antes, despues=despues, borde_inf=grosor))

    def imagen(self, ruta, ancho_cm=None, ancho_emu=None, jc="center", despues=120):
        datos = pathlib.Path(ruta).read_bytes()
        rId = f"rIdImg{self.img_counter}"
        self.imagenes.append((rId, f"image{self.img_counter}.png", datos))
        self.img_counter += 1
        
        w_px, h_px = _tamano_png(datos)
        
        if ancho_emu:
            cx = ancho_emu
            cy = int(ancho_emu * (h_px / w_px))
        elif ancho_cm:
            cx = int(ancho_cm * EMU_POR_CM)
            cy = int(cx * (h_px / w_px))
        else:
            cx = w_px * 9525
            cy = h_px * 9525
            
        xml_img = f"""
        <w:r>
          <w:drawing>
            <wp:inline distT="0" distB="0" distL="0" distR="0">
              <wp:extent cx="{cx}" cy="{cy}"/>
              <wp:effectExtent l="0" t="0" r="0" b="0"/>
              <wp:docPr id="{self.img_counter}" name="Imagen {self.img_counter}"/>
              <wp:cNvGraphicFramePr>
                <a:graphicFrameLocks xmlns:a="{NS_A}" noChangeAspect="1"/>
              </wp:cNvGraphicFramePr>
              <a:graphic xmlns:a="{NS_A}">
                <a:graphicData uri="{NS_PIC}">
                  <pic:pic xmlns:pic="{NS_PIC}">
                    <pic:nvPicPr>
                      <pic:cNvPr id="{self.img_counter}" name="Imagen {self.img_counter}"/>
                      <pic:cNvPicPr/>
                    </pic:nvPicPr>
                    <pic:blipFill>
                      <a:blip r:embed="{rId}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/>
                      <a:stretch><a:fillRect/></a:stretch>
                    </pic:blipFill>
                    <pic:spPr>
                      <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                      <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                    </pic:spPr>
                  </pic:pic>
                </a:graphicData>
              </a:graphic>
            </wp:inline>
          </w:drawing>
        </w:r>
        """
        self.add(parrafo(xml_img, jc=jc, despues=despues, mantener=True))

    def pie_figura(self, texto):
        self.add(parrafo(runs_con_marcas(texto, sz=18, color="595959"), jc="center", antes=40, despues=240))

    def tabla(self, filas, anchos, encabezado=True, sz=18, relleno_enc="1F4E79", relleno_alt="F2F6FA"):
        tbl = ['<w:tbl>', '<w:tblPr><w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/><w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tblBorders></w:tblPr>']
        
        tbl.append('<w:tblGrid>')
        for a in anchos:
            tbl.append(f'<w:gridCol w:w="{int(a * 567)}"/>')
        tbl.append('</w:tblGrid>')
        
        for i, fila in enumerate(filas):
            es_enc = encabezado and i == 0
            tbl.append('<w:tr>')
            for j, celda in enumerate(fila):
                tcpr = []
                tcpr.append(f'<w:tcW w:w="{int(anchos[j] * 567)}" w:type="dxa"/>')
                if es_enc:
                    tcpr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{relleno_enc}"/>')
                elif i % 2 == 1:
                    tcpr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{relleno_alt}"/>')
                
                tcpr_xml = f'<w:tcPr>{"".join(tcpr)}</w:tcPr>'
                color = "FFFFFF" if es_enc else "000000"
                negrita = es_enc
                
                r = run(celda, sz=sz, color=color, negrita=negrita)
                tbl.append(f'<w:tc>{tcpr_xml}{parrafo(r, jc="center", antes=40, despues=40)}</w:tc>')
            tbl.append('</w:tr>')
            
        tbl.append('</w:tbl>')
        self.add("".join(tbl))
        self.espacio(240)

    def guardar(self, destino, sect_pr=None):
        if sect_pr:
            self.sect_pr = sect_pr
            
        xml_doc = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="{NS_A}" xmlns:pic="{NS_PIC}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>
{"".join(self.body_xml)}
{self.sect_pr}
</w:body>
</w:document>
"""
        rels_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        rels_xml += '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        rels_xml += '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
        rels_xml += '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>'
        
        for rId, nombre, _ in self.imagenes:
            rels_xml += f'<Relationship Id="{rId}" Type="{TIPO_IMAGEN}" Target="media/{nombre}"/>'
        rels_xml += '</Relationships>'

        destino = pathlib.Path(destino)
        
        # If template doesn't exist or is empty, we create a valid minimal zip
        # using Python's zipfile, however here we assume template should exist for styles
        # If not, it will crash but since it's a docx builder template is required
        with zipfile.ZipFile(self.plantilla, 'r') as zin, zipfile.ZipFile(destino, 'w') as zout:
            for item in zin.infolist():
                if item.filename not in ('word/document.xml', 'word/_rels/document.xml.rels'):
                    zout.writestr(item, zin.read(item.filename))
            zout.writestr('word/document.xml', xml_doc)
            zout.writestr('word/_rels/document.xml.rels', rels_xml)
            for _, nombre, datos in self.imagenes:
                zout.writestr(f'word/media/{nombre}', datos)
