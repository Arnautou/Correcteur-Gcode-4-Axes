import os
import re
from pathlib import Path
import customtkinter as ctk
import sys
from pathlib import Path

def resource_path(rel):
    """Chemin valide en dev ET dans l'exe PyInstaller."""
    base = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return Path(base) / rel
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

EXTENSIONS_GCODE = ('.txt', '.nc', '.tap', '.gcode', '.ngc', '.ncc', '.cnc', '.mpf')


def corriger_lignes(lignes, mode, f_seuil, f_remplacement, f_z=300):
    """Applique les corrections G-code."""
    nouvelles = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        ligne_clean = ligne.strip()

        # 1) Correction des G1 A seul (sauf mode "standard")
        if mode != 'standard' and ligne_clean.startswith('G1') \
                and 'A' in ligne_clean \
                and not any(c in ligne_clean for c in ('X', 'Y', 'Z')):
            a_val = re.search(r'A([-+]?[0-9]*\.?[0-9]+)', ligne_clean)
            f_val = re.search(r'F([-+]?[0-9]*\.?[0-9]+)', ligne_clean)
            if a_val and f_val:
                a = a_val.group(1)
                f = float(f_val.group(1))
                indent = ligne[:len(ligne) - len(ligne.lstrip())]
                if f < f_seuil:
                    nouvelles.append(f'{indent}G1 A{a} F{f_remplacement}\n')
                else:
                    nouvelles.append(ligne)
                i += 1
                continue

        # 2) Correction G93 + G1 Z A (toujours)
        if ligne_clean == 'G93' and i + 1 < len(lignes):
            suiv = lignes[i + 1].strip()
            if suiv.startswith('G1') and 'Z' in suiv and 'A' in suiv:
                z_val = re.search(r'Z([-+]?[0-9]*\.?[0-9]+)', suiv)
                a_val = re.search(r'A([-+]?[0-9]*\.?[0-9]+)', suiv)
                f_val = re.search(r'F([-+]?[0-9]*\.?[0-9]+)', suiv)
                if z_val and a_val and f_val:
                    indent = ligne[:len(ligne) - len(ligne.lstrip())]
                    z, a, f = z_val.group(1), a_val.group(1), f_val.group(1)
                    nouvelles += [
                        f'{indent}G94\n',
                        f'{indent}G1 Z{z} F{f_z}\n',
                        f'{indent}G93\n',
                        f'{indent}G1 A{a} F{f}\n',
                        f'{indent}G94\n',
                    ]
                    i += 1
                    if i + 1 < len(lignes) and lignes[i + 1].strip() == 'G94':
                        i += 1
                    i += 1
                    continue

        nouvelles.append(ligne)
        i += 1
    return nouvelles


class CorrecteurApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Correcteur G-code 4 axes")
        self.geometry("800x780")
        self.minsize(720, 680)

        self.source_var = ctk.StringVar()
        self.dest_var = ctk.StringVar()
        self.mode_var = ctk.StringVar(value="rapide")
        self.seuil_var = ctk.StringVar(value="50")
        self.remplacement_var = ctk.StringVar(value="1000")

        self._build_ui()

    # ---------- UI ----------
    def _build_ui(self):
        # Header (logo + titre)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        self.logo_image = None
        try:
            from PIL import Image
            logo_path = resource_path("logo.png")
            if logo_path.exists():
                img = Image.open(logo_path)
                self.logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                ctk.CTkLabel(header, image=self.logo_image, text="").pack(side="left", padx=(0, 15))
        except Exception:
            pass

        tf = ctk.CTkFrame(header, fg_color="transparent")
        tf.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(tf, text="Correcteur G-code 4 axes",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(tf, text="Débloque les G93/G94 et accélère les rotations A trop lentes",
                     font=ctk.CTkFont(size=12)).pack(anchor="w")

        # Dossiers
        folders = ctk.CTkFrame(self)
        folders.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(folders, text="📁  Dossier source (à corriger)",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 4))
        r1 = ctk.CTkFrame(folders, fg_color="transparent")
        r1.pack(fill="x", padx=15, pady=(0, 12))
        ctk.CTkEntry(r1, textvariable=self.source_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r1, text="Parcourir…", width=110,
                      command=self._choisir_source).pack(side="left")

        ctk.CTkLabel(folders, text="📁  Dossier de sortie (corrigé)",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(4, 4))
        r2 = ctk.CTkFrame(folders, fg_color="transparent")
        r2.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkEntry(r2, textvariable=self.dest_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r2, text="Parcourir…", width=110,
                      command=self._choisir_dest).pack(side="left")

        # Modes
        modes = ctk.CTkFrame(self)
        modes.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(modes, text="Mode de correction",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 6))

        for val, lbl in [
            ("standard", "Standard  —  corriger.py  (aucun changement de vitesse A)"),
            ("rapide",   "Variante D  —  corrigerd.py  (F < 50 → F1000)"),
            ("modere",   "Variante M  —  corrigerm.py  (F < 100 → F800)"),
            ("custom",   "Personnalisé  (choisir seuil et remplacement)"),
        ]:
            ctk.CTkRadioButton(modes, text=lbl, variable=self.mode_var,
                               value=val, command=self._on_mode_change
                               ).pack(anchor="w", padx=25, pady=3)

        crow = ctk.CTkFrame(modes, fg_color="transparent")
        crow.pack(fill="x", padx=25, pady=(8, 15))
        ctk.CTkLabel(crow, text="Seuil :").pack(side="left")
        self.seuil_entry = ctk.CTkEntry(crow, textvariable=self.seuil_var, width=80)
        self.seuil_entry.pack(side="left", padx=(4, 25))
        ctk.CTkLabel(crow, text="Remplacement :").pack(side="left")
        self.rempl_entry = ctk.CTkEntry(crow, textvariable=self.remplacement_var, width=90)
        self.rempl_entry.pack(side="left", padx=4)

        # Bouton + progression
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(fill="x", padx=20, pady=10)
        self.btn_corriger = ctk.CTkButton(act, text="▶  Corriger",
                                          height=44,
                                          font=ctk.CTkFont(size=15, weight="bold"),
                                          command=self._lancer)
        self.btn_corriger.pack(fill="x")
        self.progress = ctk.CTkProgressBar(act, height=10)
        self.progress.pack(fill="x", pady=(10, 0))
        self.progress.set(0)

        # Journal
        lf = ctk.CTkFrame(self)
        lf.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        ctk.CTkLabel(lf, text="Journal",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 4))
        self.log_box = ctk.CTkTextbox(lf, wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log_box.configure(state="disabled")

        self._on_mode_change()

    # ---------- Slots ----------
    def _on_mode_change(self):
        st = "normal" if self.mode_var.get() == "custom" else "disabled"
        self.seuil_entry.configure(state=st)
        self.rempl_entry.configure(state=st)

    def _choisir_source(self):
        d = filedialog.askdirectory(title="Dossier source")
        if d:
            self.source_var.set(d)

    def _choisir_dest(self):
        d = filedialog.askdirectory(title="Dossier de sortie")
        if d:
            self.dest_var.set(d)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    # ---------- Action ----------
    def _lancer(self):
        source = self.source_var.get().strip()
        dest = self.dest_var.get().strip()

        if not source or not os.path.isdir(source):
            messagebox.showerror("Erreur", "Choisis un dossier source valide.")
            return
        if not dest:
            messagebox.showerror("Erreur", "Choisis un dossier de sortie.")
            return
        if os.path.abspath(source) == os.path.abspath(dest):
            messagebox.showerror("Erreur", "Source et sortie doivent être différents.")
            return

        mode = self.mode_var.get()
        if mode == "standard":
            f_seuil, f_rempl = None, None
        elif mode == "rapide":
            f_seuil, f_rempl = 50, 1000
        elif mode == "modere":
            f_seuil, f_rempl = 100, 800
        else:
            try:
                f_seuil = float(self.seuil_var.get())
                f_rempl = float(self.remplacement_var.get())
            except ValueError:
                messagebox.showerror("Erreur", "Valeurs personnalisées invalides.")
                return

        self.btn_corriger.configure(state="disabled", text="⏳ Correction en cours…")
        self.progress.set(0)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        try:
            self._traiter(source, dest, mode, f_seuil, f_rempl)
        except Exception as e:
            self._log(f"❌ Erreur : {e}")
            messagebox.showerror("Erreur", str(e))
        finally:
            self.btn_corriger.configure(state="normal", text="▶  Corriger")

    def _traiter(self, source, dest, mode, f_seuil, f_rempl):
        src_p, dest_p = Path(source), Path(dest)
        dest_p.mkdir(parents=True, exist_ok=True)

        fichiers = sorted([f for f in src_p.iterdir()
                           if f.is_file() and f.suffix.lower() in EXTENSIONS_GCODE])

        if not fichiers:
            self._log(f"⚠️  Aucun fichier G-code dans : {source}")
            self._log(f"   Extensions reconnues : {', '.join(EXTENSIONS_GCODE)}")
            return

        self._log(f"Mode : {mode}  |  {len(fichiers)} fichier(s)\n")
        ok = 0
        for idx, fichier in enumerate(fichiers, 1):
            try:
                with open(fichier, 'r', encoding='utf-8', errors='replace') as f:
                    lignes = f.readlines()
                nouvelles = corriger_lignes(lignes, mode, f_seuil, f_rempl, 300)
                with open(dest_p / fichier.name, 'w', encoding='utf-8') as f:
                    f.writelines(nouvelles)
                self._log(f"✅  {fichier.name}")
                ok += 1
            except Exception as e:
                self._log(f"❌  {fichier.name} : {e}")
            self.progress.set(idx / len(fichiers))
            self.update_idletasks()

        self._log(f"\n✅ Terminé : {ok}/{len(fichiers)} fichier(s) → {dest}")
        messagebox.showinfo("Terminé", f"{ok}/{len(fichiers)} fichier(s) corrigé(s).\n\n{dest}")


if __name__ == "__main__":
    CorrecteurApp().mainloop()