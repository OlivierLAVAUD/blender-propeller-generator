# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [1.0.3] - 2026-10-21

### Modifié

- Toute l'interface de l'add-on s'affiche en anglais quelle que soit la langue
  de Blender : les sections (Presets, Output…), les libellés et valeurs des
  propriétés (Blades, Smooth Shading, Cylinder, Linear…) et les menus ne sont
  plus traduits par le catalogue global de Blender (`Lamelles`, `Sortie`,
  `Aucun`…). Contexte de traduction propre à l'extension.
- Descriptions des propriétés, listes déroulantes et messages de l'opérateur
  traduits en anglais.

## [1.0.2] - 2026-10-21

### Corrigé

- Longueur de pale calculée à partir de la racine réellement rentrée dans le
  moyeu : la pointe atteint désormais le diamètre nominal (auparavant elle
  s'arrêtait au diamètre moins l'enfoncement de racine).
- Jeu du carénage : `Shroud Offset` est un jeu **radial** réel (et non la moitié)
  et peut être négatif (recouvrement).
- Preset **Pullcopter** : l'anneau extérieur est soudé à la pointe des pales
  (recouvrement 0,5 mm), formant une pièce monobloc comme le jouet réel.

## [1.0.1] - 2026-10-21

### Ajouté

- Sections de paramètres repliables : cliquer sur le titre d'une section
  (Presets, Propeller, Blade, Airfoils, Hub & Shaft, Spinner, Shroud, Output)
  pour afficher ou masquer ses réglages. Les sections avancées sont repliées
  par défaut.

## [1.0.0] - 2026-10-21

Première version publique.

### Corrigé

- Section de pale plane (sweep appliqué en rotation) : suppression du repli de la pale
  sur elle-même lorsque la corde augmente.
- Racine de pale rentrée dans le moyeu (`root_inset`) au lieu d'être tangente à sa surface.
- Formule d'ogive corrigée : rayon maximal proche de `spinner_diameter / 2`, nez en Bézier,
  raccord tangent au moyeu.
- Paraboloïde du spinner retravaillé (profil et raccord).
- Corde de pointe non nulle : ratio borné à 99,5 % et corde minimale de 2 %.
- Shroud décollé de la pointe des pales (offset minimal de 0,5 mm).
- Cube du cutter d'alésage D corrigé (il coupait tout le diamètre).
- Cutter d'alésage dimensionné sur les bornes réelles du moyeu.
- Chanfrein d'alésage implémenté (biseau bmesh), `shaft_chamfer` n'est plus ignoré.
- Booléens séquentiels pale par pale, avec validation du résultat et repli de solveur
  (`MANIFOLD` → `EXACT` → `FLOAT`) : `EXACT` pouvait renvoyer un maillage vide sans erreur.
- Union de secours (jointure) si tous les solveurs échouent.
- Matériau unique : plus de slot vide utilisé par les faces ; nœud Principled trouvé par type.
- UV (smart project), lissage par angle (35°), normales cohérentes.
- Orientation Z-up : la pointe ne part plus vers le bas.
- Conversion mm → m (échelle par défaut 0,001) et pose au sol (`ground`).
- `Reset Defaults` réinitialise toutes les propriétés, y compris les énumérations,
  les vecteurs (`keyway_size`, `color`) et les presets.

### Ajouté

- Paramètres `scale`, `ground`, `uv_unwrap`.
- Presets réinitialisés avant application : plus de résidus du preset précédent.
- Validation des paramètres avant génération (erreurs explicites).
- Nettoyage robuste des objets temporaires (`_remove_object`).
- Extension Blender (`blender_manifest.toml`), script de build et documentation.

### Modifié

- Version `1.0.0`, compatible Blender 4.2+.
- Structure du dépôt : code dans `__init__.py`, métadonnées dans `blender_manifest.toml`.
