import re
import sys

if len(sys.argv) < 3:
    print("Utilisation : python corriger.py fichier_entree.txt fichier_sortie.txt")
    sys.exit(1)

fichier_entree = sys.argv[1]
fichier_sortie = sys.argv[2]

with open(fichier_entree, 'r') as f:
    lignes = f.readlines()

nouvelles_lignes = []
i = 0
while i < len(lignes):
    ligne = lignes[i]
    ligne_clean = ligne.strip()

    # Détection : ligne G1 avec uniquement A et F (pas de X, Y, Z)
    if ligne_clean.startswith('G1') and 'A' in ligne_clean and not any(c in ligne_clean for c in ['X', 'Y', 'Z']):
        a_val = re.search(r'A([-+]?[0-9]*\.?[0-9]+)', ligne_clean)
        f_val = re.search(r'F([-+]?[0-9]*\.?[0-9]+)', ligne_clean)

        if a_val and f_val:
            a = a_val.group(1)
            f = float(f_val.group(1))
            indent = ligne[:len(ligne) - len(ligne.lstrip())]

            # Si la vitesse est trop basse (< 50 deg/min), la remplacer par une valeur rapide
            if f < 100:
                nouvelles_lignes.append(f'{indent}G1 A{a} F800\n')
            else:
                nouvelles_lignes.append(ligne)  # On garde la ligne telle quelle
            i += 1
            continue

    # Détection des mouvements avec Z ET A (correction d'origine)
    if ligne_clean == 'G93' and i + 1 < len(lignes):
        ligne_suivante = lignes[i+1].strip()
        if ligne_suivante.startswith('G1') and 'Z' in ligne_suivante and 'A' in ligne_suivante:
            z_val = re.search(r'Z([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)
            a_val = re.search(r'A([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)
            f_val = re.search(r'F([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)

            if z_val and a_val and f_val:
                z = z_val.group(1)
                a = a_val.group(1)
                f = f_val.group(1)
                indent = ligne[:len(ligne) - len(ligne.lstrip())]

                nouvelles_lignes.append(f'{indent}G94\n')
                nouvelles_lignes.append(f'{indent}G1 Z{z} F300\n')
                nouvelles_lignes.append(f'{indent}G93\n')
                nouvelles_lignes.append(f'{indent}G1 A{a} F{f}\n')
                nouvelles_lignes.append(f'{indent}G94\n')

                i += 1
                if i + 1 < len(lignes) and lignes[i+1].strip() == 'G94':
                    i += 1
                i += 1
                continue

    nouvelles_lignes.append(ligne)
    i += 1

with open(fichier_sortie, 'w') as f:
    f.writelines(nouvelles_lignes)

print(f"✅ Fichier corrigé généré : {fichier_sortie}")