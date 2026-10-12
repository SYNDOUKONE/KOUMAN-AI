# Rapport de travail — Constitution du corpus Baoulé–Dioula

## 1. Contexte

Dans le cadre du projet de développement d’un assistant multilingue capable de traiter le Baoulé et le Dioula, un travail de recherche, de collecte, d’analyse et de préparation de ressources linguistiques a été réalisé.

L’objectif principal de ces travaux est de constituer une base de données linguistique exploitable pour les futures étapes de développement et d’adaptation de modèles d’intelligence artificielle.

## 2. Missions réalisées

Les travaux réalisés ont porté sur :

- l’identification de ressources linguistiques existantes ;
- la recherche de corpus Baoulé et Dioula ;
- l’analyse de leur contenu et de leur structure ;
- la collecte des ressources accessibles ;
- le nettoyage des données ;
- la normalisation des textes ;
- la suppression des doublons exacts ;
- le contrôle de la qualité technique ;
- la séparation et la vérification des ensembles train, validation et test ;
- la documentation des sources et de leurs limites ;
- la préparation des données pour une future validation linguistique par des locuteurs natifs.

## 3. Ressources étudiées

### 3.1 Ressources Baoulé

#### R001 — Mozilla Common Voice Baoulé

Ressource audio et transcription provenant de Mozilla Common Voice.

Après nettoyage :

- 5 623 clips validés ;
- environ 14,35 heures de données ;
- 876 phrases sources ;
- nettoyage des chemins et des textes ;
- vérification de la présence des fichiers audio ;
- suppression des doublons exacts.

Le corpus est conservé avec sa provenance afin de faciliter la traçabilité.

#### R002 — Baule Speech Dataset

Ressource publiée sur Zenodo contenant des enregistrements Baoulé accompagnés de transcriptions.

Après contrôle :

- 539 paires audio-transcription exploitables ;
- 0 transcription vide ;
- 0 doublon exact ;
- suppression des numéros éditoriaux placés au début de certaines phrases.

La ressource brute contenait également des transcriptions ne disposant pas toutes d’un fichier audio correspondant.

#### R003 — AfriSpeech Baoulé

Ressource audio Baoulé issue du projet AfriSpeech.

Après nettoyage :

- 2 657 clips ;
- environ 8,08 heures ;
- 2 307 données d’entraînement ;
- 125 données de validation ;
- 225 données de test ;
- 0 texte vide ;
- 0 doublon exact.

Une structure de validation linguistique a également été préparée afin de permettre une future vérification par des locuteurs natifs.

#### R004 — Google WaxalNLP Baoulé

Ressource audio et texte issue de WaxalNLP.

Après nettoyage :

- 1 212 enregistrements conservés ;
- 968 données d’entraînement ;
- 122 données de validation ;
- 122 données de test ;
- 4 doublons supprimés.

Cette ressource pourra notamment être utilisée pour les travaux liés aux données vocales Baoulé.

## 4. Ressources Dioula

### R005 — AfriSpeech Jula/Dioula

Ressource audio et transcription issue d’AfriSpeech.

Après nettoyage :

- 5 485 clips conservés ;
- 5 018 données d’entraînement ;
- 258 données de validation ;
- 209 données de test ;
- 1 doublon supprimé ;
- nettoyage des marqueurs numériques éditoriaux.

Une attention particulière est nécessaire concernant la variété linguistique : la ressource provient du Burkina Faso et doit donc être validée avant son adaptation directe au contexte du Dioula ivoirien.

### R006 — SuzuyaXIII Dioula

Ressource textuelle contenant des données Français–Dioula ainsi que des données provenant de plusieurs sources.

Après traitement :

- 2 452 entrées conservées ;
- normalisation de la structure ;
- conservation de la provenance ;
- identification de 144 paires Français–Dioula répétées.

Les répétitions n’ont pas été supprimées automatiquement afin de préserver la provenance des différentes sources.

Cette ressource ne contient pas d’audio.

### R007 — Koumankan

Deux ressources Koumankan ont été identifiées sur Hugging Face.

Cependant, leur téléchargement est actuellement soumis à des restrictions d’accès.

La ressource a donc été documentée mais n’a pas été intégrée au corpus final.

Cette décision permet de conserver une trace de la ressource sans contourner les conditions d’accès.

### R008 — hf_fr_dioula_full

Ressource parallèle Français–Dioula accessible publiquement.

Données brutes :

- 25 642 paires ;
- train : 20 513 ;
- validation : 2 564 ;
- test : 2 565.

Après nettoyage et dédoublonnage :

- 12 664 paires uniques ;
- train : 8 072 ;
- validation : 2 145 ;
- test : 2 447 ;
- 0 paire vide ;
- 0 doublon source-cible ;
- aucune paire identique présente dans plusieurs splits.

Une stratégie de priorité test → validation → train a été utilisée afin d’éviter les fuites de données entre les différents ensembles.

## 5. Corpus Baoulé consolidé

Les quatre principales ressources Baoulé nettoyées ont été regroupées dans un corpus consolidé.

Répartition :

| Ressource | Nombre de phrases |
|---|---:|
| R001 | 5 623 |
| R002 | 539 |
| R003 | 2 657 |
| R004 | 1 212 |
| **Total** | **10 031** |

Fichier :



Un contrôle des doublons exacts entre les quatre ressources n’a identifié aucune phrase commune.

## 6. Validation linguistique

La validation technique des ressources a été réalisée.

Des fichiers de préparation à la validation linguistique ont également été créés pour permettre l’intervention de locuteurs natifs.

La validation linguistique complète reste une étape à réaliser.

Elle devra notamment porter sur :

- la compréhension des phrases ;
- la naturalité des formulations ;
- la correction des transcriptions ;
- la pertinence des traductions ;
- les variantes linguistiques ;
- les corrections proposées par les locuteurs natifs.

## 7. Organisation et traçabilité

Le projet est organisé en plusieurs niveaux :

-  : ressources originales collectées ;
-  : ressources étudiées et préparées ;
-  : données nettoyées ;
-  : espace prévu pour les annotations ;
-  : fichiers de validation ;
-  : corpus consolidés ;
-  : documentation du projet ;
-  : inventaire des ressources.

Cette organisation permet de conserver la provenance des données et de suivre les différentes étapes de transformation.

## 8. Difficultés rencontrées

Plusieurs difficultés ont été identifiées :

- hétérogénéité des formats des ressources ;
- présence de doublons ;
- présence de marqueurs éditoriaux dans certaines transcriptions ;
- absence d’audio pour certaines transcriptions ;
- différences possibles entre variétés linguistiques ;
- ressources Hugging Face soumises à des restrictions d’accès ;
- licences parfois non clairement identifiées au niveau de la ressource ;
- nécessité d’une validation par des locuteurs natifs.

## 9. Modèle de base envisagé

Pour les futures étapes de traduction automatique, le projet pourra s’appuyer sur un modèle multilingue pré-entraîné tel que :



Ce modèle pourra servir de base à une éventuelle adaptation sur les données Français–Dioula après validation et préparation du corpus.

L’adaptation du modèle n’a pas encore été réalisée dans le cadre de ces deux jours de travail.

## 10. Résultats obtenus

À l’issue du travail réalisé :

- 8 ressources ont été identifiées et documentées ;
- 7 ressources accessibles ou exploitables ont été traitées ;
- 1 ressource reste inaccessible en raison de restrictions d’accès ;
- les principales ressources Baoulé ont été nettoyées ;
- plusieurs ressources Dioula ont été nettoyées et normalisées ;
- un corpus Baoulé consolidé de 10 031 phrases a été constitué ;
- un corpus Français–Dioula de 12 664 paires uniques a été nettoyé ;
- un inventaire des ressources a été créé ;
- la documentation du projet a été structurée ;
- les fichiers nécessaires à une future validation linguistique ont été préparés.

## 11. Prochaines étapes

Les prochaines étapes recommandées sont :

1. réaliser la validation avec des locuteurs natifs Baoulé et Dioula ;
2. corriger les données selon les retours linguistiques ;
3. compléter les annotations ;
4. vérifier les licences de chaque ressource ;
5. rechercher et supprimer les éventuels doublons entre différentes sources ;
6. finaliser le corpus destiné à l’entraînement ou à l’adaptation ;
7. préparer les données pour le modèle de traduction ;
8. effectuer une première évaluation du modèle ;
9. intégrer le modèle dans l’API du projet.

## 12. Conclusion

Le travail réalisé a permis de poser une première base structurée pour la constitution d’un corpus Baoulé–Dioula.

La démarche adoptée repose sur la traçabilité des sources, le nettoyage des données, le contrôle de leur qualité technique et la préparation d’une validation linguistique humaine.

Le corpus obtenu constitue une base de travail pour les prochaines étapes du projet, notamment la validation par des locuteurs natifs et l’adaptation éventuelle d’un modèle multilingue aux besoins spécifiques du Baoulé et du Dioula.
