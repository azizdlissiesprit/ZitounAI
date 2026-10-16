# M1 · Leaf diseases — notebooks

| | |
|---|---|
| Data | Uğuz & Uysal — `Olive_Leaf_Disease_Datasets_After_Preprocessing` (3 classes, ~7 000 images) |
| Baseline | Petit CNN (3 blocs conv, aucun transfert) |
| Modèle principal | MobileNetV3-Large ImageNet, fine-tuning en 2 phases (tête puis complet) |
| Fiabilité | Temperature scaling (T apprise sur val) + seuil de confiance 0.70 |
| Métriques | Accuracy, F1 par classe + macro, matrices de confusion, Grad-CAM, ECE |
| Export | `models/m1/` : `model.pt` (TorchScript), `model.onnx`, `model.tflite`, `classes.json`, `calibration.json`, `metadata.json` |

## Fichiers

| Fichier | Rôle |
|---|---|
| `prepare_splits.py` | Détecte les dossiers de classes et crée les splits **70/15/15 stratifiés, seed 42**, **groupés par feuille d'origine** (les variantes Roboflow d'une même feuille restent dans le même split — pas de fuite de données). Sortie : `data/processed/m1_disease/{train,val,test}/<classe>/`. |
| `m1_common.py` | Bibliothèque partagée : seeds, augmentations « photo terrain », datasets, modèles, boucle d'entraînement, métriques, Grad-CAM, calibration, exports. Importé par le notebook et `evaluate_field.py`. |
| `train_m1.ipynb` | Tout le pipeline : splits → EDA → baseline → MobileNetV3 → évaluation → calibration → seuil → export. |
| `evaluate_field.py` | Évalue le modèle exporté sur des photos terrain (`field_test/`) avec les mêmes métriques que l'API. |

## 1 · Préparer les données (une seule fois)

```bash
cd notebooks/m1_disease
python prepare_splits.py --src "C:/.../Olive_Leaf_Disease_Datasets_After_Preprocessing"
# splits -> <repo>/data/processed/m1_disease/ (idempotent : relancer ne fait rien sans --force)
```

## 2 · Entraîner (Google Colab recommandé, T4 GPU)

1. Copiez dans votre Drive :
   - le dataset sous `ZitounAI/Olive_Leaf_Disease_Datasets_After_Preprocessing/` ;
   - `train_m1.ipynb`, `m1_common.py`, `prepare_splits.py` sous `ZitounAI/notebooks/m1_disease/`.
2. Ouvrez `train_m1.ipynb` dans Colab : `Exécution → Modifier le type d'exécution → T4 GPU`.
3. Exécutez de haut en bas (~30–40 min sur T4). Le notebook détecte Colab tout seul,
   monte le Drive, prépare les splits localement puis entraîne.
4. La dernière cellule produit un zip des artefacts : téléchargez-le, dézippez-le dans
   `models/m1/` du repo, puis partagez-le : `python scripts/models.py push m1`
   (voir `models/README.md`, il faut `HF_MODELS_REPO` et `HF_TOKEN` dans `.env`).

En local (CPU possible) : exécutez le notebook depuis ce dossier avec les epochs réduits
(cellule de configuration) — comptez quelques heures sur CPU pour la version complète.

## 3 · Évaluer sur photos terrain

```bash
mkdir -p field_test/healthy field_test/peacock_spot field_test/aculus_olearius
# … déposez-y les photos prises chez les agriculteurs (ou à plat dans field_test/)
python evaluate_field.py          # rapport -> outputs/field_report/ (CSV + JSON + matrice)
```

## Conventions équipe

- Les notebooks s'exécutent de haut en bas sur un noyau frais ; **sorties dépouillées avant commit** (CONTRIBUTING.md).
- Figures produites dans `outputs/` et données dans `data/` : **jamais commités**.
- Le résultat attendu par l'équipe : `models/m1/model.pt` (+ fichiers annexes) sur Hugging Face.
