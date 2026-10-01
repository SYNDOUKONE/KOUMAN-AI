"""
Générateur du Gabarit de Jeu de Test Sacré pour KOUMAN AI (Étape 1).

Crée un jeu de test de 150 phrases conversationnelles du quotidien
(salutations, questions du quotidien, commerce, santé, transports, services).
Format : id, fr, dyu, domaine, traducteur_1, traducteur_2
"""

import os
import csv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT_DIR, "data", "test_sacre.csv")

phrases_base = [
    # 1. Salutations & Politesse
    ("Bonjour", "Aw ni sɔgɔma", "salutations_politesse"),
    ("Bonjour à vous", "Aw ni tile", "salutations_politesse"),
    ("Bonsoir", "Aw ni wula", "salutations_politesse"),
    ("Bonne nuit", "Aw ni su", "salutations_politesse"),
    ("Comment vas-tu ?", "I ka kɛnɛ wa?", "salutations_politesse"),
    ("Comment allez-vous ?", "Aw ka kɛnɛ wa?", "salutations_politesse"),
    ("As-tu passé une bonne nuit ?", "Hɛrɛ sira?", "salutations_politesse"),
    ("As-tu passé une bonne journée ?", "Hɛrɛ tilena?", "salutations_politesse"),
    ("Merci beaucoup", "I ni cɛ kosɛbɛ", "salutations_politesse"),
    ("Merci pour votre aide", "I ni cɛ dɛmɛ la", "salutations_politesse"),
    ("S'il te plaît", "Dusu la", "salutations_politesse"),
    ("À demain", "An bɛ bɛn sini", "salutations_politesse"),
    ("À plus tard", "An bɛ bɛn kɔfɛ", "salutations_politesse"),
    ("Au revoir", "An bɛ bɛn kɔfɛ", "salutations_politesse"),
    ("Soyez le bienvenu", "I bisimila", "salutations_politesse"),
    ("Pardonnez-moi", "Yafama n ma", "salutations_politesse"),
    ("Que la paix soit avec vous", "Hɛrɛ ka kɛ aw fɛ", "salutations_politesse"),
    ("Bonne arrivée à la maison", "Sɔn ka ɲi", "salutations_politesse"),

    # 2. Commerce & Marché
    ("Combien ça coûte ?", "Jɔn bi di?", "commerce_marche"),
    ("Quel est le prix de ceci ?", "Sɔngɔ ka di?", "commerce_marche"),
    ("C'est trop cher", "Sɔngɔ ka gɛlɛn kosɛbɛ", "commerce_marche"),
    ("Diminue un peu le prix", "Sɔngɔ dɔ dɔgɔya", "commerce_marche"),
    ("Je vais au marché", "N bɛ taa sugu la", "commerce_marche"),
    ("Venez acheter mon pain", "Aw ye na ne ta buru san", "commerce_marche"),
    ("Venez acheter de la nourriture", "Aw ye na domuni san", "commerce_marche"),
    ("Avez-vous du poisson ?", "Jɛgɛ bɛ aw fɛ wa?", "commerce_marche"),
    ("Donne-moi du riz s'il te plaît", "Malo di n ma dusu", "commerce_marche"),
    ("Je veux acheter de l'eau", "N bɛ fɛ ka jii san", "commerce_marche"),
    ("Je n'ai pas d'argent", "Wari tɛ n fɛ", "commerce_marche"),
    ("Prends ton argent", "I ta wari ta", "commerce_marche"),
    ("Où puis-je acheter du pain ?", "N bɛ se ka buru san min?", "commerce_marche"),
    ("Le marché est fermé aujourd'hui", "Sugu tugulɛn bɛ bi", "commerce_marche"),

    # 3. Questions Fréquentes & Chatbot (Kouman AI)
    ("Comment t'appelles-tu ?", "I tɔgɔ bi di?", "questions_frequentes"),
    ("Je m'appelle Kouman", "Ne tɔgɔ bi Kouman", "questions_frequentes"),
    ("Parles-tu dioula ?", "I bɛ dioula kan mɛn wa?", "questions_frequentes"),
    ("Je comprends le dioula", "Ne bɛ dioula kan mɛn", "questions_frequentes"),
    ("Je ne comprends pas", "N tɛ a mɛn", "questions_frequentes"),
    ("Pouvez-vous m'aider ?", "Aw bɛ se ka n dɛmɛ wa?", "questions_frequentes"),
    ("Que veux-tu dire ?", "I bɛ mun fɔ?", "questions_frequentes"),
    ("Répète s'il te plaît", "A fɔ tugu dusu la", "questions_frequentes"),
    ("Parle doucement", "Fɔ mounimouni", "questions_frequentes"),
    ("Je cherche une information", "N bɛ kunnafoni dɔ ɲini", "questions_frequentes"),
    ("Avez-vous une question ?", "Ɲininkali dɔ bɛ aw fɛ wa?", "questions_frequentes"),
    ("Merci pour votre réponse", "I ni cɛ i jaabi la", "questions_frequentes"),

    # 4. Services Digitaux & Mobile
    ("Où est l'agence la plus proche ?", "Neton so bɛ min?", "services_digital"),
    ("Je veux recharger mon téléphone", "N bɛ fɛ ka ne ta fonɛn mara", "services_digital"),
    ("Comment envoyer de l'argent ?", "N bɛ wari ci cogo di?", "services_digital"),
    ("Mon téléphone ne marche pas", "Ne ta fonɛn tɛ baara kɛ", "services_digital"),
    ("Quel est ton numéro de téléphone ?", "I ta fonɛn nɔmbɔro bi di?", "services_digital"),
    ("Envoyez-moi un message", "Kuma ci n ma", "services_digital"),

    # 5. Santé & Bien-être
    ("Je suis malade", "N bɛ bana la", "sante_bienetre"),
    ("J'ai mal à la tête", "Koun-dimi bɛ n na", "sante_bienetre"),
    ("Où se trouve l'hôpital ?", "Lopitani bɛ min?", "sante_bienetre"),
    ("Donne-moi de l'eau à boire", "Jii di n ma", "sante_bienetre"),
    ("Appelez un docteur s'il te plaît", "Dɔkɔtɔrɔ wele dusu la", "sante_bienetre"),
    ("Repose-toi bien", "I lafiya kosɛbɛ", "sante_bienetre"),
    ("Est-ce que tu vas mieux ?", "I ka kɛnɛ dɔɔnin wa?", "sante_bienetre"),

    # 6. Déplacements & Orientation
    ("Où vas-tu aujourd'hui ?", "I bɛ taa min bi?", "deplacement_orientation"),
    ("Je vais à la maison", "N bɛ taa so la", "deplacement_orientation"),
    ("Le travail est difficile mais il est bon", "Baara ka gɛlɛn nka a ka ɲi", "deplacement_orientation"),
    ("L'enfant dort dans la chambre", "Denmisɛn bɛ sunɔgɔ so kɔnɔ", "famille_vie_quotidienne"),
    ("Il fait chaud aujourd'hui", "Goueni bɛ bi", "famille_vie_quotidienne"),
    ("La pluie va tomber", "San bɛ na ben", "famille_vie_quotidienne"),
    ("Nous allons manger ensemble", "An bɛ taa domuni kɛ ɲɔgɔn fɛ", "famille_vie_quotidienne"),
    ("Attends-moi ici", "N kɔnɔ yan", "famille_vie_quotidienne"),
    ("On se voit plus tard", "An bɛ ben kɔfɛ", "famille_vie_quotidienne")
]

prompts_extension = [
    ("Quel heure est-il ?", "Wati bi di?", "vie_quotidienne"),
    ("Où habites-tu ?", "I bɛ sigi min?", "vie_quotidienne"),
    ("Quelle est votre profession ?", "I ta baara bi di?", "vie_quotidienne"),
    ("J'aime la langue dioula", "Dioula kan ka di n ye", "vie_quotidienne"),
    ("Est-ce loin d'ici ?", "A janman bɛ yan wa?", "deplacement_orientation"),
    ("C'est tout près d'ici", "A surumani bɛ yan", "deplacement_orientation"),
    ("Où est le restaurant ?", "Domuniso bɛ min?", "commerce_marche"),
    ("Donne-moi le reçu", "Sɛbɛn di n ma", "commerce_marche"),
    ("Avez-vous de la monnaie ?", "Wari misɛn bɛ i fɛ wa?", "commerce_marche"),
    ("Je cherche la gare de bus", "N bɛ kisi ɲini", "deplacement_orientation"),
    ("À quelle heure part le bus ?", "Kisi bɛ bɔ wati jumɛn?", "deplacement_orientation"),
    ("Bon voyage à vous", "Sira ɲuman", "salutations_politesse"),
    ("Prends soin de toi", "I yɛrɛ mara kosɛbɛ", "salutations_politesse"),
    ("Que Dieu vous bénisse", "Ala ka duba i ye", "salutations_politesse"),
    ("Merci beaucoup mon frère", "I ni cɛ ne balima", "salutations_politesse"),
    ("Merci beaucoup ma sœur", "I ni cɛ ne balima muso", "salutations_politesse"),
    ("Comment va la famille ?", "Somɔgɔw ka kɛnɛ wa?", "famille_vie_quotidienne"),
    ("Tout le monde va bien", "Mɔgɔ bɛɛ ka kɛnɛ", "famille_vie_quotidienne"),
    ("L'enfant va à l'école", "Denmisɛn bɛ taa kalan-so la", "famille_vie_quotidienne"),
    ("J'apprends le dioula tous les jours", "N bɛ dioula kan kalan don bɛɛ", "questions_frequentes"),
    ("Est-ce que le service est disponible ?", "Baara bɛ yen wa?", "services_digital"),
    ("Pouvez-vous m'expliquer cela ?", "I bɛ se ka o ɲɛfɔ n ye wa?", "questions_frequentes"),
    ("C'est une bonne idée", "Hakili ɲuman bɛ o la", "questions_frequentes"),
    ("Je suis d'accord avec toi", "N sɔnna i ta kuma ma", "questions_frequentes"),
    ("Je ne suis pas d'accord", "N tɛ sɔn o ma", "questions_frequentes"),
    ("Attendez une minute s'il vous plaît", "Aw ye dɔɔnin kɔnɔ dusu la", "salutations_politesse"),
    ("C'est très gentil de votre part", "O ka ɲi kosɛbɛ", "salutations_politesse"),
    ("Bonne chance pour ton travail", "Baara ɲuman kɛ i ye", "salutations_politesse"),
    ("Puis-je poser une question ?", "N bɛ se ka ɲininkali dɔ kɛ wa?", "questions_frequentes"),
    ("Où est le marché central ?", "Sugu ba bɛ min?", "commerce_marche"),
    ("Combien coûte ce vêtement ?", "Dereke nin sɔngɔ bi di?", "commerce_marche"),
    ("J'ai fini mon travail", "N ta baara banna", "travail_quotidien"),
    ("Le travail commence à quelle heure ?", "Baara bɛ daminɛ wati jumɛn?", "travail_quotidien"),
    ("Nous devons travailler dur", "An ka kan ka baara gɛlɛn kɛ", "travail_quotidien"),
    ("Il y a beaucoup de monde ici", "Mɔgɔ caman bɛ yan", "vie_quotidienne"),
    ("Il n'y a personne dans la maison", "Mɔgɔ tɛ so kɔnɔ", "vie_quotidienne"),
    ("Avez-vous besoin d'aide ?", "Dɛmɛ bɛ i fɛ wa?", "questions_frequentes"),
    ("Je suis très content aujourd'hui", "Ne nisɔndiyalen bɛ bi", "famille_vie_quotidienne"),
    ("Ne t'inquiète pas", "I kana hami", "salutations_politesse"),
    ("Tout va bien se passer", "Ko bɛɛ bɛna ɲɛ", "salutations_politesse"),
    ("À ce soir", "An bɛ wula la", "salutations_politesse"),
    ("Passe une bonne soirée", "Wula ɲuman kɛ i ye", "salutations_politesse"),
    ("À tout à l'heure", "An bɛ dɔɔnin kɔfɛ", "salutations_politesse"),
    ("Prends ce livre", "Sɛbɛn nin ta", "questions_frequentes"),
    ("Écris ton nom ici", "I tɔgɔ sɛbɛ yan", "questions_frequentes"),
    ("Quelle est la date d'aujourd'hui ?", "Bi don bi di?", "vie_quotidienne"),
    ("Le soleil brille fort", "Tile ka gɛlɛn", "vie_quotidienne"),
    ("La nuit est calme", "Su ka di", "vie_quotidienne"),
    ("Qu'est-ce que tu en penses ?", "I hakili bi di o la?", "questions_frequentes"),
    ("C'est parfait", "A ka ɲi kosɛbɛ", "questions_frequentes"),
    ("Je ne me sens pas bien", "N tɛ n yɛrɛ mɛn ka ɲi", "sante_bienetre"),
    ("Où se trouve la pharmacie de garde ?", "Furuso bɛ min bi?", "sante_bienetre"),
    ("Prends ce médicament", "Furu nin ta", "sante_bienetre"),
    ("Bois beaucoup d'eau", "Jii caman mi", "sante_bienetre"),
    ("Ferme la porte s'il te plaît", "Da tugu dusu la", "vie_quotidienne"),
    ("Ouvre la fenêtre", "Fɛnɛtiri dayɛlɛ", "vie_quotidienne"),
    ("Entrez s'il vous plaît", "Aw ye don dusu la", "salutations_politesse"),
    ("Asseyez-vous ici", "Aw ye sigi yan", "salutations_politesse"),
    ("Que voulez-vous boire ?", "Aw bɛ fɛ ka mun mi?", "commerce_marche"),
    ("Apporte-moi un verre d'eau", "Jii kɔpɔ di n ma", "commerce_marche"),
    ("Le repas est prêt", "Domuni labɛnna", "famille_vie_quotidienne"),
    ("C'est très délicieux", "Domuni ka di kosɛbɛ", "famille_vie_quotidienne"),
    ("Merci pour ce bon repas", "I ni cɛ domuni ɲuman la", "salutations_politesse"),
    ("Où pouvons-nous nous rencontrer ?", "An bɛ se ka bɛn min?", "deplacement_orientation"),
    ("Je t'attends devant le bâtiment", "N bɛ i kɔnɔ so ɲɛfɛ", "deplacement_orientation"),
    ("Ne sois pas en retard", "I kana kɔfɛbɔ", "deplacement_orientation"),
    ("Je suis en chemin", "N bɛ sira la", "deplacement_orientation"),
    ("Je suis arrivé", "N seera", "deplacement_orientation"),
    ("Félicitations pour ton succès", "I ni cɛ sɔrɔ la", "salutations_politesse"),
    ("Bon anniversaire", "Sankɛnɛ ɲuman kɛ i ye", "salutations_politesse"),
    ("Bonne année à toute la famille", "San kura ɲuman somɔgɔw ye", "salutations_politesse"),
    ("Que cette journée soit belle", "Don nin ka ɲɛ i ye", "salutations_politesse"),
    ("Restons en contact", "An ka to kuma la", "questions_frequentes"),
    ("Envoie-moi un message plus tard", "Kuma ci n ma kɔfɛ", "services_digital"),
    ("Mon réseau ne marche pas bien", "Rɛzo tɛ baara kɛ ka ɲi", "services_digital"),
    ("Où puis-je trouver un taxi ?", "N bɛ takisi sɔrɔ min?", "deplacement_orientation"),
    ("Combien pour aller au centre-ville ?", "Sugu ba la taa sɔngɔ bi di?", "deplacement_orientation"),
    ("C'est bon, nous pouvons partir", "A ka ɲi, an bɛ se ka taa", "deplacement_orientation")
]

all_pairs = phrases_base + prompts_extension

def generate_csv():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    rows = []
    for idx, (fr, dyu, dom) in enumerate(all_pairs, start=1):
        rows.append({
            "id": f"TEST_SACRE_{idx:03d}",
            "fr": fr,
            "dyu": dyu,
            "domaine": dom,
            "traducteur_1": "LOCUTEUR_NATIVE_1_A_VALIDER",
            "traducteur_2": "LOCUTEUR_NATIVE_2_A_VALIDER"
        })
    
    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "fr", "dyu", "domaine", "traducteur_1", "traducteur_2"])
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"✅ Gabarit de jeu de test sacré généré dans : {OUTPUT_PATH} ({len(rows)} phrases conversationnelles)")

if __name__ == "__main__":
    generate_csv()
