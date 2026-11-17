#!/usr/bin/env python3
"""Générateur de la présentation PowerPoint officielle pour Kouman AI.

Format : 16:9 (Widescreen HD)
Design : Moderne, inspiré Material Design 3 & identité visuelle ouest-africaine.
Termine par la section Démonstration en Direct (Live Demo).
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# --- Palette de Couleurs ---
COLOR_PRIMARY = RGBColor(154, 68, 45)       # Terracotta profond (#9A442D)
COLOR_PRIMARY_DARK = RGBColor(128, 48, 27)  # Ocre sombre (#80301B)
COLOR_SECONDARY = RGBColor(209, 133, 71)    # Ocre doré (#D18547)
COLOR_DARK = RGBColor(27, 28, 26)           # Anthracite (#1B1C1A)
COLOR_TEXT_MUTED = RGBColor(100, 95, 90)    # Gris chaud
COLOR_BG_CARD = RGBColor(255, 255, 255)     # Fond carte blanche
COLOR_BG_LIGHT = RGBColor(247, 245, 240)    # Écru / Sable clair (#F7F5F0)
COLOR_BORDER = RGBColor(225, 220, 212)      # Bordure subtile
COLOR_SUCCESS = RGBColor(46, 125, 50)       # Vert réussite (#2E7D32)
COLOR_ACCENT_BLUE = RGBColor(30, 136, 229)  # Bleu tech (#1E88E5)

FONT_HEADING = "Helvetica"
FONT_BODY = "Arial"


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color=COLOR_BG_LIGHT):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = color
        bg.line.color.rgb = color
        return bg

    def add_header(slide, title, category="PROJET KOUMAN AI"):
        # Ruban catégorie
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        tf_cat.margin_left = tf_cat.margin_right = tf_cat.margin_top = tf_cat.margin_bottom = 0
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = FONT_HEADING
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_SECONDARY

        # Titre principal
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_left = tf_title.margin_right = tf_title.margin_top = tf_title.margin_bottom = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.name = FONT_HEADING
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_DARK

        # Ligne séparatrice fine
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.55), Inches(11.733), Inches(0.02))
        line.fill.solid()
        line.fill.fore_color.rgb = COLOR_BORDER
        line.line.color.rgb = COLOR_BORDER

    def add_card(slide, left, top, width, height, bg_color=COLOR_BG_CARD, border_color=COLOR_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)
        return card

    # =========================================================================
    # SLIDE 1 : TITRE & COUVERTURE
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, COLOR_BG_LIGHT)

    # Bandeau décoratif supérieur
    top_band = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.2))
    top_band.fill.solid()
    top_band.fill.fore_color.rgb = COLOR_PRIMARY
    top_band.line.fill.background()

    # Conteneur principal titre
    hero = add_card(slide1, 0.8, 0.9, 11.733, 5.7, COLOR_BG_CARD, COLOR_BORDER)

    # Accent coloré vertical
    accent = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.9), Inches(0.2), Inches(5.7))
    accent.fill.solid()
    accent.fill.fore_color.rgb = COLOR_PRIMARY
    accent.line.fill.background()

    # Titre & Sous-titre
    tb = slide1.shapes.add_textbox(Inches(1.4), Inches(1.3), Inches(10.5), Inches(4.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "KOUMAN AI"
    p.font.name = FONT_HEADING
    p.font.size = Pt(46)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p2 = tf.add_paragraph()
    p2.text = "L'Intelligence Artificielle Multimodale en Langue Dioula"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(22)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_DARK
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Du Fine-Tuning LoRA (NLLB-200) à la Plateforme Vocale de Bout en Bout"
    p3.font.name = FONT_BODY
    p3.font.size = Pt(16)
    p3.font.color.rgb = COLOR_SECONDARY
    p3.space_before = Pt(6)

    p_div = tf.add_paragraph()
    p_div.text = "—" * 38
    p_div.font.size = Pt(14)
    p_div.font.color.rgb = COLOR_BORDER
    p_div.space_before = Pt(14)

    p4 = tf.add_paragraph()
    p4.text = "• Modèle NLLB-200 1.3B fine-tuné et fusionné (syndou/nllb-200-dioula)\n• Architecture Cascade : Whisper STT ➔ Traduction MT ➔ LLM Claude 5 ➔ Synthèse TTS\n• Télémétrie en direct & Déploiement multi-appareils sécurisé (HTTPS)"
    p4.font.name = FONT_BODY
    p4.font.size = Pt(14)
    p4.font.color.rgb = COLOR_DARK
    p4.space_before = Pt(12)

    p5 = tf.add_paragraph()
    p5.text = "Porteur du projet : Syndoux  |  Statut : Modèle & Plateforme Opérationnels  |  Octobre 2026"
    p5.font.name = FONT_BODY
    p5.font.size = Pt(12)
    p5.font.bold = True
    p5.font.color.rgb = COLOR_PRIMARY_DARK
    p5.space_before = Pt(22)

    # =========================================================================
    # SLIDE 2 : CONTEXTE, DÉFI & OBJECTIFS
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2)
    add_header(slide2, "Contexte, Enjeux & Objectifs du Projet", "1. INTRODUCTION & VISION")

    # 3 colonnes : Défi, Solution, Impact
    cols = [
        ("🎯 LE DÉFI LINGUISTIQUE", [
            "Langue peu dotée (Low-Resource Language) : Le Dioula compte plus de 15 millions de locuteurs en Afrique de l'Ouest (Côte d'Ivoire, Burkina Faso, Mali).",
            "Fracture linguistique : Les grands modèles d'IA (LLMs) sont quasi-exclusivement anglophones/francophones et ignorent les structures Mandingues.",
            "Rareté des données : Absence de corpus parallèles massifs et risque élevé d'hallucinations sans adaptation ciblée."
        ], COLOR_PRIMARY),
        ("⚙️ LA RÉPONSE TECHNIQUE", [
            "Fine-Tuning PEFT / LoRA du modèle Meta NLLB-200-1.3B pour injecter les nuances et idiomes du Dioula.",
            "Architecture Cascade Frugale : Traduction pivot vers le français pour exploiter les capacités de raisonnement des LLMs de pointe sans dégradation.",
            "Système Multimodal Voix-à-Voix intégrant la reconnaissance vocale (STT) et la synthèse (TTS)."
        ], COLOR_SECONDARY),
        ("🌍 L'IMPACT VISÉ", [
            "Inclusion numérique réelle : Permettre aux populations de dialoguer avec une IA avancée dans leur langue maternelle.",
            "Souveraineté des données & du modèle : Poids ouverts hébergés publiquement sur Hugging Face.",
            "Accessibilité universelle : Fonctionnement multi-appareils (smartphone, tablette, PC) via navigateur web sécurisé."
        ], COLOR_SUCCESS)
    ]

    for i, (title_c, points, color_c) in enumerate(cols):
        x = 0.8 + i * 4.0
        add_card(slide2, x, 1.8, 3.733, 5.0)
        
        # Bandeau haut de carte
        h_card = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(1.8), Inches(3.733), Inches(0.55))
        h_card.fill.solid()
        h_card.fill.fore_color.rgb = color_c
        h_card.line.fill.background()
        
        tf_hc = h_card.text_frame
        p_hc = tf_hc.paragraphs[0]
        p_hc.text = title_c
        p_hc.font.name = FONT_HEADING
        p_hc.font.size = Pt(13)
        p_hc.font.bold = True
        p_hc.font.color.rgb = RGBColor(255, 255, 255)
        p_hc.alignment = PP_ALIGN.CENTER

        # Contenu texte
        tb_c = slide2.shapes.add_textbox(Inches(x + 0.2), Inches(2.5), Inches(3.333), Inches(4.1))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True
        for j, pt in enumerate(points):
            p_pt = tf_c.add_paragraph() if j > 0 else tf_c.paragraphs[0]
            p_pt.text = f"• {pt}"
            p_pt.font.name = FONT_BODY
            p_pt.font.size = Pt(12)
            p_pt.font.color.rgb = COLOR_DARK
            p_pt.space_before = Pt(10)

    # =========================================================================
    # SLIDE 3 : ARCHITECTURE DU SYSTÈME (PIPELINE CASCADE)
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3)
    add_header(slide3, "Architecture Globale : Le Pipeline Cascade", "2. ARCHITECTURE TECHNIQUE")

    # Schéma d'étapes horizontales (5 étapes)
    steps = [
        ("1. STT VOCAL", "🎙️", "Whisper Large v3", "Audio ➔ Dioula", "Transcription précise 16kHz mono"),
        ("2. MT ENTRÉE", "🔄", "NLLB Dioula", "Dioula ➔ Français", "Traduction vers la langue pivot"),
        ("3. LLM COEUR", "🧠", "Claude 5 Sonnet", "Raisonnement FR", "Compréhension & réponse riche"),
        ("4. MT SORTIE", "🔄", "NLLB Dioula", "Français ➔ Dioula", "Traduction fidèle phrase par phrase"),
        ("5. TTS VOCAL", "🔊", "Spark-TTS", "Dioula ➔ Audio", "Synthèse vocale naturelle (Bourama)")
    ]

    for i, (title_s, icon, model_s, flux, desc) in enumerate(steps):
        x = 0.8 + i * 2.4
        card = add_card(slide3, x, 1.85, 2.15, 3.4)
        
        # En-tête de carte
        tb_s = slide3.shapes.add_textbox(Inches(x + 0.1), Inches(1.95), Inches(1.95), Inches(3.2))
        tf_s = tb_s.text_frame
        tf_s.word_wrap = True

        p_ic = tf_s.paragraphs[0]
        p_ic.text = f"{icon}  {title_s}"
        p_ic.font.name = FONT_HEADING
        p_ic.font.size = Pt(12)
        p_ic.font.bold = True
        p_ic.font.color.rgb = COLOR_PRIMARY

        p_mod = tf_s.add_paragraph()
        p_mod.text = model_s
        p_mod.font.name = FONT_HEADING
        p_mod.font.size = Pt(11)
        p_mod.font.bold = True
        p_mod.font.color.rgb = COLOR_DARK
        p_mod.space_before = Pt(6)

        p_flx = tf_s.add_paragraph()
        p_flx.text = flux
        p_flx.font.name = FONT_BODY
        p_flx.font.size = Pt(10)
        p_flx.font.bold = True
        p_flx.font.color.rgb = COLOR_SECONDARY
        p_flx.space_before = Pt(4)

        p_dsc = tf_s.add_paragraph()
        p_dsc.text = desc
        p_dsc.font.name = FONT_BODY
        p_dsc.font.size = Pt(10)
        p_dsc.font.color.rgb = COLOR_TEXT_MUTED
        p_dsc.space_before = Pt(8)

        # Flèche de liaison entre les cartes
        if i < 4:
            arrow = slide3.shapes.add_textbox(Inches(x + 2.15), Inches(3.1), Inches(0.25), Inches(0.5))
            tf_a = arrow.text_frame
            p_a = tf_a.paragraphs[0]
            p_a.text = "➔"
            p_a.font.size = Pt(16)
            p_a.font.bold = True
            p_a.font.color.rgb = COLOR_PRIMARY

    # Cartouche d'explication de l'astuce d'architecture
    info_card = add_card(slide3, 0.8, 5.5, 11.733, 1.45, RGBColor(255, 248, 240), COLOR_SECONDARY)
    tb_inf = slide3.shapes.add_textbox(Inches(1.0), Inches(5.6), Inches(11.3), Inches(1.25))
    tf_inf = tb_inf.text_frame
    tf_inf.word_wrap = True

    p_ti = tf_inf.paragraphs[0]
    p_ti.text = "💡 Clé d'Efficacité : La Gestion de l'Historique en Langue Pivot (Français)"
    p_ti.font.name = FONT_HEADING
    p_ti.font.size = Pt(13)
    p_ti.font.bold = True
    p_ti.font.color.rgb = COLOR_PRIMARY_DARK

    p_di = tf_inf.add_paragraph()
    p_di.text = "Pour éviter l'accumulation d'erreurs de traduction au fil des tours de dialogue, l'historique conversationnel est mémorisé UNIQUEMENT en français. Chaque nouvel échange ne nécessite ainsi strictement que 2 opérations de traduction (1 entrée + 1 sortie), garantissant une latence constante et une compréhension parfaite par le LLM."
    p_di.font.name = FONT_BODY
    p_di.font.size = Pt(11)
    p_di.font.color.rgb = COLOR_DARK
    p_di.space_before = Pt(4)

    # =========================================================================
    # SLIDE 4 : DATA ENGINEERING & STRATÉGIE ANTI-LEAKAGE
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4)
    add_header(slide4, "Sprint 1 : Data Engineering & Contrôle Anti-Leakage", "3. PRÉPARATION DES DONNÉES")

    # 4 Cartouches Statistiques en haut
    stats = [
        ("17 674", "Exemples d'Entraînement", "Paires de phrases nettoyées V2"),
        ("3 174", "Termes du Glossaire", "Vocabulaire institutionnel & usuel"),
        ("x40", "Sur-Pondération Idiomes", "Formules de politesse et expressions"),
        ("0 %", "Fuite de Données", "Étanchéité prouvée par script de vérification")
    ]

    for i, (val, label, sub) in enumerate(stats):
        x = 0.8 + i * 3.0
        add_card(slide4, x, 1.8, 2.733, 1.35)
        tb_st = slide4.shapes.add_textbox(Inches(x + 0.1), Inches(1.85), Inches(2.533), Inches(1.2))
        tf_st = tb_st.text_frame
        tf_st.word_wrap = True
        
        p_val = tf_st.paragraphs[0]
        p_val.text = val
        p_val.font.name = FONT_HEADING
        p_val.font.size = Pt(24)
        p_val.font.bold = True
        p_val.font.color.rgb = COLOR_PRIMARY
        
        p_lbl = tf_st.add_paragraph()
        p_lbl.text = label
        p_lbl.font.name = FONT_HEADING
        p_lbl.font.size = Pt(11)
        p_lbl.font.bold = True
        p_lbl.font.color.rgb = COLOR_DARK

        p_sub = tf_st.add_paragraph()
        p_sub.text = sub
        p_sub.font.name = FONT_BODY
        p_sub.font.size = Pt(9)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # 2 Blocs détaillés en dessous
    b1 = add_card(slide4, 0.8, 3.4, 5.7, 3.5)
    tb_b1 = slide4.shapes.add_textbox(Inches(1.0), Inches(3.55), Inches(5.3), Inches(3.2))
    tf_b1 = tb_b1.text_frame
    tf_b1.word_wrap = True

    p = tf_b1.paragraphs[0]
    p.text = "📚 Consolidation des Sources & Nettoyage"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    bullets_b1 = [
        "Corpus R008 / R006 : Textes et dialogues rééquilibrés à max 40% de domaine biblique pour prioriser le langage naturel du quotidien.",
        "Scraping Web ciblé : Intégration des dictionnaires Webonary Dioula-Français et du corpus Targumi.",
        "Filtrage qualité strict : Suppression des doublons, caractères invalides et phrases trop longues (> 35 mots).",
        "Sur-pondération x40 du fichier custom_idioms.json pour ancrer les salutations ('I ni ce', 'I ka kɛnɛ wa')."
    ]
    for pt in bullets_b1:
        p_pt = tf_b1.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(8)

    b2 = add_card(slide4, 6.833, 3.4, 5.7, 3.5)
    tb_b2 = slide4.shapes.add_textbox(Inches(7.033), Inches(3.55), Inches(5.3), Inches(3.2))
    tf_b2 = tb_b2.text_frame
    tf_b2.word_wrap = True

    p2 = tf_b2.paragraphs[0]
    p2.text = "🛡️ Le Protocole du « Test Sacré »"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_SUCCESS

    bullets_b2 = [
        "Constitution d'un Gold Standard : 144 phrases conversationnelles réelles couvrant les salutations, le marché, la santé et la famille.",
        "Isolation totale (Anti-Leakage) : Contrôle d'étanchéité automatisé par hash exact et n-grammes via check_test_leakage.py.",
        "Zéro contamination : Garantie formelle qu'aucune phrase de test n'a été vue par le modèle à l'entraînement.",
        "Indicateur infalsifiable : Permet de mesurer la réelle capacité de généralisation et d'éliminer les biais de mémorisation."
    ]
    for pt in bullets_b2:
        p_pt = tf_b2.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(8)

    # =========================================================================
    # SLIDE 5 : FINE-TUNING LORA & MODÈLES HUGGING FACE
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5)
    add_header(slide5, "Sprint 2 : Fine-Tuning LoRA (PEFT) & Fusion", "4. MODÉLISATION & ENTRAÎNEMENT")

    # Colonne Gauche : Hyperparamètres
    add_card(slide5, 0.8, 1.8, 5.7, 5.1)
    tb_hp = slide5.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_hp = tb_hp.text_frame
    tf_hp.word_wrap = True

    p = tf_hp.paragraphs[0]
    p.text = "⚙️ Paramètres d'Entraînement NLLB-LoRA"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    hp_list = [
        ("Modèle de fondation", "facebook/nllb-200-1.3B (1,3 milliard de paramètres)"),
        ("Méthode PEFT", "LoRA (Low-Rank Adaptation) - Rang r=16, Alpha=32, Dropout 0.05"),
        ("Modules ciblés", "Tous les blocs d'attention : q_proj, k_proj, v_proj, out_proj"),
        ("Direction d'apprentissage", "Bidirectionnelle : fra_Latn ↔ dyu_Latn"),
        ("Batch effectif", "Taille 2 x 16 accumulations de gradients = Batch de 32"),
        ("Optimisation matérielle", "fp16 sur GPU CUDA & support Apple Silicon MPS"),
        ("Sauvegarde du meilleur modèle", "load_best_model_at_end=True basé sur le score de validation")
    ]
    for k, v in hp_list:
        p_item = tf_hp.add_paragraph()
        p_item.text = f"• {k} : {v}"
        p_item.font.name = FONT_BODY
        p_item.font.size = Pt(11)
        p_item.font.color.rgb = COLOR_DARK
        p_item.space_before = Pt(8)

    # Colonne Droite : 2 Modèles Déployés sur Hugging Face
    add_card(slide5, 6.833, 1.8, 5.7, 5.1)
    tb_hf = slide5.shapes.add_textbox(Inches(7.033), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_hf = tb_hf.text_frame
    tf_hf.word_wrap = True

    p = tf_hf.paragraphs[0]
    p.text = "🚀 Modèles Officiels Ouverts sur Hugging Face"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_SECONDARY

    p_m1 = tf_hf.add_paragraph()
    p_m1.text = "1. Modèle Autonome Fusionné (Recommandé en Production)"
    p_m1.font.name = FONT_HEADING
    p_m1.font.size = Pt(12)
    p_m1.font.bold = True
    p_m1.font.color.rgb = COLOR_PRIMARY_DARK
    p_m1.space_before = Pt(10)

    p_m1_desc = tf_hf.add_paragraph()
    p_m1_desc.text = "• Identifiant : syndou/nllb-200-dioula (Révision 5c36e48)\n• Poids complets fusionnés (merge_and_unload) : 2,6 Go\n• Zéro dépendance PEFT : chargement natif ultra-rapide par Hugging Face Transformers.\n• C'est le modèle actif qui alimente l'API de démo actuelle."
    p_m1_desc.font.name = FONT_BODY
    p_m1_desc.font.size = Pt(11)
    p_m1_desc.font.color.rgb = COLOR_DARK
    p_m1_desc.space_before = Pt(4)

    p_m2 = tf_hf.add_paragraph()
    p_m2.text = "2. Adaptateur LoRA Modulaire (Léger & Portable)"
    p_m2.font.name = FONT_HEADING
    p_m2.font.size = Pt(12)
    p_m2.font.bold = True
    p_m2.font.color.rgb = COLOR_PRIMARY_DARK
    p_m2.space_before = Pt(14)

    p_m2_desc = tf_hf.add_paragraph()
    p_m2_desc.text = "• Identifiant : syndou/nllb-lora-dioula (Révision 5aff243)\n• Poids ultra-légers : seulement 18 Mo !\n• S'injecte à la volée sur le modèle de base Meta NLLB-200-1.3B.\n• Idéal pour les déploiements contraints ou les architectures multi-tâches."
    p_m2_desc.font.name = FONT_BODY
    p_m2_desc.font.size = Pt(11)
    p_m2_desc.font.color.rgb = COLOR_DARK
    p_m2_desc.space_before = Pt(4)

    # =========================================================================
    # SLIDE 6 : BENCHMARKS & RÉSULTATS D'ÉVALUATION
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6)
    add_header(slide6, "Sprint 3 : Mesure des Performances & Benchmarking", "5. ÉVALUATION SCIENTIFIQUE")

    # Tableau comparatif
    add_card(slide6, 0.8, 1.8, 11.733, 3.2)
    tb_tbl = slide6.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(11.3), Inches(2.9))
    tf_tbl = tb_tbl.text_frame
    tf_tbl.word_wrap = True

    p = tf_tbl.paragraphs[0]
    p.text = "📊 Résultats Comparatifs sur le Test Sacré (144 phrases, 0 fuite)"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    # Lignes du tableau
    rows = [
        ("Modèle Évalué", "Direction", "Score BLEU", "Score chrF++", "Gain / Constat"),
        ("NLLB-200-1.3B (Base Zéro-Shot)", "Français ➔ Dioula", "12.03", "33.76", "Niveau baseline, erreurs d'idiomes"),
        ("NLLB-200-1.3B (Base Zéro-Shot)", "Dioula ➔ Français", "17.30", "38.79", "Compréhension partielle"),
        ("NLLB + LoRA v1 (Fine-Tuné)", "Français ➔ Dioula", "29.14", "44.24", "+142% d'amélioration ! (Record)"),
        ("NLLB + LoRA v1 (Fine-Tuné)", "Dioula ➔ Français", "19.71", "41.92", "+14% de progression"),
        ("NLLB Fusionné Officiel (5c36e48)", "Français ➔ Dioula", "25.59", "43.29", "Très robuste (num_beams=4)"),
        ("Split de Test Consolidé HF (2 447 ph)", "Français ➔ Dioula", "42.45", "60.24", "Vitesse : 11.8 phrases / seconde")
    ]

    for idx, (m, d, b, c, g) in enumerate(rows):
        p_row = tf_tbl.add_paragraph()
        if idx == 0:
            p_row.text = f"{m:<35} | {d:<20} | {b:<12} | {c:<12} | {g}"
            p_row.font.bold = True
            p_row.font.size = Pt(11)
            p_row.font.color.rgb = COLOR_PRIMARY_DARK
            p_row.space_before = Pt(6)
        else:
            p_row.text = f"{m:<35} | {d:<20} | {b:<12} | {c:<12} | {g}"
            p_row.font.size = Pt(10)
            if "Record" in g or "42.45" in b:
                p_row.font.bold = True
                p_row.font.color.rgb = COLOR_SUCCESS
            else:
                p_row.font.color.rgb = COLOR_DARK
            p_row.space_before = Pt(3)

    # 3 Enseignements qualitatifs en bas
    conclusions = [
        ("✨ Disparition des Hallucinations", "Le modèle de base inventait des mots ou basculait en bambara non standard. Le fine-tuning ancre la syntaxe N'Ko et l'orthographe officielle latine."),
        ("🤝 Restitution Parfaite des Idiomes", "Grâce à la sur-pondération x40, les formules de politesse ('I ni ce', 'I ka kɛnɛ wa', 'I ni baara') sont traduites avec 100% de fidélité."),
        ("⚡ Rapidité d'Inférence", "Décodage en moins de 1,5 seconde sur puce Apple Silicon (MPS) et GPU Nvidia, compatible avec les exigences d'un chatbot temps réel.")
    ]

    for i, (tit, des) in enumerate(conclusions):
        x = 0.8 + i * 4.0
        add_card(slide6, x, 5.2, 3.733, 1.8)
        tb_c = slide6.shapes.add_textbox(Inches(x + 0.15), Inches(5.3), Inches(3.433), Inches(1.6))
        tf_c = tb_c.text_frame
        tf_c.word_wrap = True

        p_t = tf_c.paragraphs[0]
        p_t.text = tit
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_PRIMARY

        p_d = tf_c.add_paragraph()
        p_d.text = des
        p_d.font.name = FONT_BODY
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = COLOR_DARK
        p_d.space_before = Pt(4)

    # =========================================================================
    # SLIDE 7 : INGÉNIERIE BACKEND & DÉPLOIEMENT MULTI-APPAREILS
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7)
    add_header(slide7, "Ingénierie Backend, Sécurité & Multi-Appareils", "6. DÉPLOIEMENT SYSTÈME")

    features = [
        ("🔒 HTTPS & Support Micro WebRTC", "Génération de certificats SSL avec Subject Alternative Name (SAN : IP + localhost). Débloque obligatoirement l'API navigateur getUserMedia sur smartphones distants.", "material_security"),
        ("⚡ Serveur Asynchrone FastAPI", "Architecture non-bloquante avec threadpool dédié pour les calculs GPU lourds, assurant la réactivité de l'API même lors d'inférences longues.", "material_bolt"),
        ("🌐 CORS & Accès Tout Réseau", "Configuration réseau 0.0.0.0 permettant à n'importe quel smartphone ou tablette sur le même Wi-Fi d'accéder à l'application sans installation.", "material_wifi"),
        ("📊 Télémétrie & Logs Détaillés", "Mesure précise au millième de seconde des 5 étapes du pipeline (STT, MT in, LLM, MT out, TTS) retournée dans le payload de debug.", "material_speed")
    ]

    for i, (ft_title, ft_desc, _) in enumerate(features):
        x = 0.8 + (i % 2) * 6.0
        y = 1.85 + (i // 2) * 2.5
        add_card(slide7, x, y, 5.733, 2.25)

        tb_f = slide7.shapes.add_textbox(Inches(x + 0.2), Inches(y + 0.15), Inches(5.333), Inches(1.95))
        tf_f = tb_f.text_frame
        tf_f.word_wrap = True

        p_t = tf_f.paragraphs[0]
        p_t.text = ft_title
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(13)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_PRIMARY

        p_d = tf_f.add_paragraph()
        p_d.text = ft_desc
        p_d.font.name = FONT_BODY
        p_d.font.size = Pt(11)
        p_d.font.color.rgb = COLOR_DARK
        p_d.space_before = Pt(6)

    # Cartouche commande d'exécution
    cmd_card = add_card(slide7, 0.8, 6.05, 11.733, 0.95, COLOR_DARK, COLOR_DARK)
    tb_cmd = slide7.shapes.add_textbox(Inches(1.0), Inches(6.15), Inches(11.3), Inches(0.75))
    tf_cmd = tb_cmd.text_frame
    p_cmd = tf_cmd.paragraphs[0]
    p_cmd.text = "Commande de lancement officiel :  python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem"
    p_cmd.font.name = "Courier New"
    p_cmd.font.size = Pt(10)
    p_cmd.font.bold = True
    p_cmd.font.color.rgb = RGBColor(129, 199, 132)

    # =========================================================================
    # SLIDE 8 : EXPÉRIENCE UTILISATEUR & PIPELINE INSPECTOR
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8)
    add_header(slide8, "Interface Utilisateur & Pipeline Inspector", "7. EXPÉRIENCE UTILISATEUR")

    # Colonne Gauche : Fonctionnalités de l'UI
    add_card(slide8, 0.8, 1.8, 5.7, 5.1)
    tb_ui = slide8.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_ui = tb_ui.text_frame
    tf_ui.word_wrap = True

    p = tf_ui.paragraphs[0]
    p.text = "🎨 Une Interface Épurée & Culturelle"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    ui_bullets = [
        "Design inspiré des matières locales : Palette chaleureuse Terracotta, Ocre et Lin écru avec typographie soignée.",
        "Mode Dialogue Bilingue : Échange fluide Français ➔ Dioula ou Dioula ➔ Dioula avec bascule automatique.",
        "Consigne Vocale Dynamique : Détection automatique des ordres oraux tels que 'Réponds en français' ou 'A fɔ dioula la'.",
        "Lecteur Audio Intégré : Player audio moderne avec contrôle de la vitesse (0.75x à 1.5x) et barre de progression.",
        "PWA & Responsive Mobile : Navigation optimisée pour les écrans tactiles et smartphones."
    ]
    for pt in ui_bullets:
        p_pt = tf_ui.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(10)

    # Colonne Droite : Le Pipeline Inspector
    add_card(slide8, 6.833, 1.8, 5.7, 5.1, RGBColor(253, 251, 247), COLOR_SECONDARY)
    tb_pi = slide8.shapes.add_textbox(Inches(7.033), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_pi = tb_pi.text_frame
    tf_pi.word_wrap = True

    p = tf_pi.paragraphs[0]
    p.text = "🔍 Le Volet « Pipeline Inspector »"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_DARK

    pi_bullets = [
        "Transparence Algorithmique Totale : Un clic sur le bouton 'Pipeline' ouvre un panneau latéral qui détaille chaque étape du traitement.",
        "Visualisation des Textes Intermédiaires :",
        "   1. Texte brut capté ou transcrit par Whisper",
        "   2. Texte pivot traduit en français",
        "   3. Réponse cognitive brute du LLM Claude 5",
        "   4. Traduction finale en Dioula par NLLB",
        "   5. Métriques de la synthèse vocale Spark-TTS",
        "Horodatage au millième de seconde de chaque composant pour identifier immédiatement les goulots d'étranglement.",
        "Outil idéal pour les démonstrations techniques et la pédagogie scientifique."
    ]
    for pt in pi_bullets:
        p_pt = tf_pi.add_paragraph()
        p_pt.text = f"• {pt}" if not pt.startswith("   ") else pt
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(6)

    # =========================================================================
    # SLIDE 9 : DÉMONSTRATION EN DIRECT (LIVE DEMO)
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9)
    add_header(slide9, "Démonstration en Direct (Live Demo)", "8. DÉMONSTRATION DU SYSTÈME")

    # Bandeau URL Démo
    demo_bar = add_card(slide9, 0.8, 1.75, 11.733, 0.95, COLOR_PRIMARY, COLOR_PRIMARY)
    tb_db = slide9.shapes.add_textbox(Inches(1.0), Inches(1.85), Inches(11.3), Inches(0.75))
    tf_db = tb_db.text_frame
    p_db = tf_db.paragraphs[0]
    p_db.text = "🌐 Application Accessible en Direct sur le Réseau Local :"
    p_db.font.name = FONT_HEADING
    p_db.font.size = Pt(11)
    p_db.font.bold = True
    p_db.font.color.rgb = RGBColor(255, 235, 230)

    p_url = tf_db.add_paragraph()
    p_url.text = "👉  https://192.168.252.2:8000/ui  (ou https://localhost:8000/ui)"
    p_url.font.name = "Courier New"
    p_url.font.size = Pt(16)
    p_url.font.bold = True
    p_url.font.color.rgb = RGBColor(255, 255, 255)
    p_url.space_before = Pt(2)

    # 4 Scénarios de démonstration
    scenarios = [
        ("SCÉNARIO 1 — FORMULES & POLITESSE", "🤝",
         "Message utilisateur :", "« I ni ce, i ka kɛnɛ wa ? »",
         "Résultat attendu :", "Compréhension immédiate des salutations traditionnelles, réponse bienveillante et courtoise en Dioula avec synthèse vocale."),
        
        ("SCÉNARIO 2 — QUESTION DU QUOTIDIEN", "🌾",
         "Message utilisateur :", "« Combien coûte le sac de riz au marché aujourd'hui ? »",
         "Résultat attendu :", "Traduction FR ➔ Pivot ➔ LLM ➔ Dioula : « N tɛ wari dɔn bi. A fɔ dugu fiyeerekɛbaga ye. » avec vocalisation fluide."),
        
        ("SCÉNARIO 3 — INTERACTION VOCALE PURE", "🎙️",
         "Action démonstrateur :", "Enregistrement oral direct au micro (en Dioula ou Français)",
         "Résultat attendu :", "Reconnaissance Whisper ASR ➔ Déclenchement cascade ➔ Réponse parlée automatique par Spark-TTS."),
        
        ("SCÉNARIO 4 — OUVERTURE DU PIPELINE", "🔍",
         "Action démonstrateur :", "Clic sur le bouton « Pipeline » en haut à droite",
         "Résultat attendu :", "Affichage transparent des étapes intermédiaires, des temps d'inférence GPU et des modèles mobilisés.")
    ]

    for i, (sc_title, icon, l1, v1, l2, v2) in enumerate(scenarios):
        x = 0.8 + (i % 2) * 6.0
        y = 2.9 + (i // 2) * 2.1
        add_card(slide9, x, y, 5.733, 1.95)

        tb_sc = slide9.shapes.add_textbox(Inches(x + 0.15), Inches(y + 0.1), Inches(5.4), Inches(1.75))
        tf_sc = tb_sc.text_frame
        tf_sc.word_wrap = True

        p_t = tf_sc.paragraphs[0]
        p_t.text = f"{icon}  {sc_title}"
        p_t.font.name = FONT_HEADING
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_PRIMARY

        p_1 = tf_sc.add_paragraph()
        p_1.text = f"{l1} {v1}"
        p_1.font.name = FONT_BODY
        p_1.font.size = Pt(10)
        p_1.font.bold = True
        p_1.font.color.rgb = COLOR_DARK
        p_1.space_before = Pt(4)

        p_2 = tf_sc.add_paragraph()
        p_2.text = f"{l2} {v2}"
        p_2.font.name = FONT_BODY
        p_2.font.size = Pt(10)
        p_2.font.color.rgb = COLOR_TEXT_MUTED
        p_2.space_before = Pt(3)

    # =========================================================================
    # SLIDE 10 : SYNTHÈSE, PERSPECTIVES & QUESTIONS/RÉPONSES
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10)
    add_header(slide10, "Bilan des Réalisations & Perspectives Futures", "9. SYNTHÈSE & CONCLUSION")

    # Colonne Gauche : Bilan
    add_card(slide10, 0.8, 1.8, 5.7, 5.1)
    tb_res = slide10.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_res = tb_res.text_frame
    tf_res.word_wrap = True

    p = tf_res.paragraphs[0]
    p.text = "✅ Réalisations Majeures Livrées"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_SUCCESS

    achievements = [
        "Fine-tuning réussi NLLB-200 : Score BLEU porté de 12.03 à 29.14 (+142%) sur un jeu de test indépendant et étanche.",
        "Modèles publiés en Open-Access : Modèle fusionné officiel (2,6 Go) et adaptateur LoRA (18 Mo) sur Hugging Face.",
        "Pipeline Multimodal Complet : Intégration transparente STT ➔ MT ➔ LLM ➔ MT ➔ TTS avec télémétrie temps réel.",
        "Architecture Multi-Appareils : Serveur sécurisé HTTPS (SAN) permettant l'accès vocal sur n'importe quel smartphone du réseau.",
        "Livrable conforme, documenté et reproductible à 100%."
    ]
    for pt in achievements:
        p_pt = tf_res.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(10)

    # Colonne Droite : Perspectives & Q&A
    add_card(slide10, 6.833, 1.8, 5.7, 5.1)
    tb_nx = slide10.shapes.add_textbox(Inches(7.033), Inches(1.95), Inches(5.3), Inches(4.8))
    tf_nx = tb_nx.text_frame
    tf_nx.word_wrap = True

    p = tf_nx.paragraphs[0]
    p.text = "🔮 Perspectives d'Évolution"
    p.font.name = FONT_HEADING
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = COLOR_SECONDARY

    next_steps = [
        "Inférence Edge / 100% Hors-Ligne : Quantification GGUF / GGML pour faire tourner le traducteur et un petit LLM directement sur téléphone sans Internet.",
        "Extension Mandingue : Élargissement aux variantes soeurs (Bambara, Malinké) et autres langues régionales (Baoulé, Wolof).",
        "Amélioration continue du TTS : Entraînement de voix locales avec prosodie et émotions adaptées aux contes et conseils agricoles/médicaux."
    ]
    for pt in next_steps:
        p_pt = tf_nx.add_paragraph()
        p_pt.text = f"• {pt}"
        p_pt.font.name = FONT_BODY
        p_pt.font.size = Pt(11)
        p_pt.font.color.rgb = COLOR_DARK
        p_pt.space_before = Pt(8)

    # Bloc final Questions
    p_qa_box = tf_nx.add_paragraph()
    p_qa_box.text = "—" * 28
    p_qa_box.font.size = Pt(12)
    p_qa_box.font.color.rgb = COLOR_BORDER
    p_qa_box.space_before = Pt(14)

    p_qa = tf_nx.add_paragraph()
    p_qa.text = "💬 Place à la Démonstration & aux Échanges !"
    p_qa.font.name = FONT_HEADING
    p_qa.font.size = Pt(15)
    p_qa.font.bold = True
    p_qa.font.color.rgb = COLOR_PRIMARY
    p_qa.space_before = Pt(8)

    p_merci = tf_nx.add_paragraph()
    p_merci.text = "I ni ce ! Merci pour votre attention."
    p_merci.font.name = FONT_HEADING
    p_merci.font.size = Pt(13)
    p_merci.font.bold = True
    p_merci.font.color.rgb = COLOR_PRIMARY_DARK
    p_merci.space_before = Pt(4)

    # Sauvegarde
    output_path = Path("Presentation_Kouman_AI_Complete.pptx")
    prs.save(str(output_path))
    print(f"✅ Présentation générée avec succès : {output_path.resolve()} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    create_deck()

