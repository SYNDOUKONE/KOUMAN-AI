# Corpus Baoulé – Dioula

## 1. Présentation

Ce projet a pour objectif de constituer un corpus linguistique exploitable pour le développement d’un assistant multilingue capable de traiter le Baoulé et le Dioula.

Le travail porte principalement sur :
- la collecte de ressources linguistiques ;
- l’analyse des corpus existants ;
- le nettoyage et la normalisation des données ;
- la constitution d’un corpus consolidé ;
- la préparation des données pour la validation linguistique ;
- la documentation des sources, licences et limites ;
- la préparation à l’adaptation d’un modèle multilingue de traduction.

## 2. Organisation du projet



## 3. Ressources collectées

### Baoulé
- R001 — Mozilla Common Voice Baoulé
- R002 — Zenodo Baule Speech Dataset
- R003 — AfriSpeech Baoulé
- R004 — Google WaxalNLP Baoulé

### Dioula
- R005 — AfriSpeech Jula/Dioula
- R006 — SuzuyaXIII Dioula
- R007 — Koumankan
- R008 — hf_fr_dioula_full

R007 a été identifié mais n’a pas été intégré au corpus en raison de restrictions d’accès.

## 4. Nettoyage des données

Les traitements réalisés comprennent notamment :
- suppression des lignes vides ;
- suppression des doublons exacts ;
- normalisation des espaces ;
- nettoyage de certains marqueurs numériques éditoriaux ;
- vérification des colonnes et des types ;
- conservation de la provenance des ressources ;
- séparation et contrôle des ensembles train, validation et test.

Les données brutes sont conservées séparément afin de préserver la traçabilité.

## 5. Résultats actuels

### Corpus Baoulé

Le corpus Baoulé consolidé contient actuellement :
- R001 : 5 623 phrases
- R002 : 539 phrases
- R003 : 2 657 phrases
- R004 : 1 212 phrases

Total : **10 031 phrases**

Fichier : 

### Corpus Dioula

Les principales ressources nettoyées comprennent :
- R005 : corpus audio + transcription ;
- R006 : ressource textuelle Français–Dioula ;
- R008 : corpus parallèle Français–Dioula.

R008 contient après nettoyage :
- Train : 8 072 paires
- Validation : 2 145 paires
- Test : 2 447 paires
- Total : **12 664 paires uniques**

Contrôles réalisés :
- 0 paire vide ;
- 0 doublon source-cible ;
- 0 paire présente dans plusieurs splits.

## 6. Validation linguistique

La validation technique des données a été réalisée sur plusieurs ressources.

La validation linguistique par des locuteurs natifs reste une étape importante du projet.

Elle devra notamment permettre de vérifier :
- la compréhension des phrases ;
- la naturalité des formulations ;
- les variantes linguistiques ;
- les erreurs de transcription ;
- les traductions ;
- les corrections proposées.

## 7. Modèle de base

Le projet pourra utiliser un modèle multilingue pré-entraîné tel que :



NLLB-200 (*No Language Left Behind*) est un modèle de traduction multilingue développé par Meta AI.

L’objectif est de pouvoir adapter un modèle pré-entraîné à partir du corpus Français–Dioula constitué et validé dans le cadre du projet.

## 8. Limites actuelles

Les principales limites identifiées sont :
- certaines ressources sont de taille limitée ;
- certaines ressources nécessitent une validation linguistique native ;
- certaines ressources Hugging Face sont soumises à des restrictions d’accès ;
- les ressources peuvent provenir de variétés linguistiques différentes ;
- les licences doivent être vérifiées au niveau de chaque ressource avant redistribution ou utilisation commerciale ;
- la validation linguistique complète reste à réaliser.

## 9. Prochaines étapes

1. Finaliser l’inventaire des ressources.
2. Réaliser la validation par des locuteurs natifs.
3. Corriger et annoter les données validées.
4. Finaliser le corpus Baoulé–Dioula.
5. Vérifier les licences et conditions d’utilisation.
6. Préparer les données pour l’adaptation du modèle.
7. Évaluer les performances du modèle.
8. Exposer le système sous forme d’API.

## 10. Traçabilité

Chaque ressource est identifiée par un identifiant unique : , , , etc.

Les données brutes, les données nettoyées, les validations et les corpus finaux sont conservés dans des répertoires distincts afin de faciliter la reproductibilité et le suivi des transformations.
