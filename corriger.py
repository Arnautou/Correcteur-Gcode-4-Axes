import re
import sys

# Vérifier les arguments
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

    # On détecte "G93" suivi d'une ligne "G1" contenant à la fois Z et A
    if ligne_clean == 'G93' and i + 1 < len(lignes):
        ligne_suivante = lignes[i+1].strip()
        if ligne_suivante.startswith('G1') and 'Z' in ligne_suivante and 'A' in ligne_suivante:
            # Extraire les valeurs numériques
            z_val = re.search(r'Z([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)
            a_val = re.search(r'A([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)
            f_val = re.search(r'F([-+]?[0-9]*\.?[0-9]+)', ligne_suivante)

            if z_val and a_val and f_val:
                z = z_val.group(1)
                a = a_val.group(1)
                f = f_val.group(1)

                # Conserver l'indentation (espaces ou tabulations)
                indent = ligne[:len(ligne) - len(ligne.lstrip())]

                # Écrire le nouveau bloc
                nouvelles_lignes.append(f'{indent}G94\n')
                nouvelles_lignes.append(f'{indent}G1 Z{z} F300\n')   # F300 comme vos autres passes Z
                nouvelles_lignes.append(f'{indent}G93\n')
                nouvelles_lignes.append(f'{indent}G1 A{a} F{f}\n')
                nouvelles_lignes.append(f'{indent}G94\n')

                # Sauter les lignes originales : G93, le G1, et le G94 qui suit
                i += 1  # on saute le G1
                if i + 1 < len(lignes) and lignes[i+1].strip() == 'G94':
                    i += 1  # on saute le G94
                i += 1  # on saute le G93 initial
                continue

    # Sinon, on garde la ligne telle quelle
    nouvelles_lignes.append(ligne)
    i += 1

# Écrire le fichier corrigé
with open(fichier_sortie, 'w') as f:
    f.writelines(nouvelles_lignes)

print(f"✅ Fichier corrigé généré : {fichier_sortie}")
print(f"   (pensez à vérifier et à sauvegarder votre original)")