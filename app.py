# -*- coding: utf-8 -*-
"""
app.py - Interface grafica para dimensionamento de vigas protendidas
         NBR 6118:2014 / Torii (2020)

Uso:  python app.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle, Circle

from geometry import RectangularSection
from materials import Concrete, PrestressSteel, CP_190_RB_CATALOG
from supports import SimplySupported, FixedFixed, Cantilever
from loads import Loads, combine_actions, Md_ULS
from stress_limits import stress_limits
from stress_check import stresses_at_section, check_stresses
from uls_flexure import MRd_simplified, Mlim_rectangular

N = 300  # pontos nos diagramas

PSI = {
    'residencial':        {'psi1': 0.4, 'psi2': 0.3},
    'comercial':          {'psi1': 0.6, 'psi2': 0.4},
    'biblioteca_arquivo': {'psi1': 0.7, 'psi2': 0.6},
    'oficina_garagem':    {'psi1': 0.6, 'psi2': 0.4},
    'vento':              {'psi1': 0.3, 'psi2': 0.0},
    'temperatura':        {'psi1': 0.5, 'psi2': 0.3},
}


def _shear(x_arr, M_arr):
    """V(x) = dM/dx por diferencas centrais."""
    return np.gradient(M_arr, x_arr)


# ─────────────────────────────────────────────────────────────────────────────
#  APLICACAO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class BeamApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Viga Protendida  –  NBR 6118:2014")
        self.geometry("1380x840")
        self.resizable(True, True)
        self._build_ui()

    # ── layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        pw = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        left = ttk.Frame(pw, width=360)
        left.pack_propagate(False)
        pw.add(left, weight=0)

        right = ttk.Frame(pw)
        pw.add(right, weight=1)

        self._build_inputs(left)
        self._build_results(right)

    # ── painel de entradas ────────────────────────────────────────────────────

    def _build_inputs(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0, bg='#f5f5f5')
        sb = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = ttk.Frame(canvas)
        win = canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>',
                   lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-e.delta / 120), 'units'))

        self.v = {}
        p = dict(padx=6, pady=3)

        def lf(title):
            f = ttk.LabelFrame(inner, text=title, padding=8)
            f.pack(fill=tk.X, padx=8, pady=5)
            return f

        def erow(f, lbl, key, val):
            r = f.grid_size()[1]
            ttk.Label(f, text=lbl).grid(row=r, column=0, sticky='w', **p)
            sv = tk.StringVar(value=str(val))
            ttk.Entry(f, textvariable=sv, width=13).grid(row=r, column=1, sticky='w', **p)
            self.v[key] = sv

        def crow(f, lbl, key, opts, val):
            r = f.grid_size()[1]
            ttk.Label(f, text=lbl).grid(row=r, column=0, sticky='w', **p)
            sv = tk.StringVar(value=val)
            ttk.Combobox(f, textvariable=sv, values=opts,
                         width=24, state='readonly').grid(row=r, column=1, sticky='w', **p)
            self.v[key] = sv

        # ── Geometria ──
        f = lf("Geometria da Secao")
        erow(f, "Largura b (m)",  'b',  0.30)
        erow(f, "Altura h (m)",   'h',  0.80)

        # ── Apoio ──
        f = lf("Apoio e Vao")
        crow(f, "Tipo de apoio", 'support',
             ['Biapoiado', 'Engastado-Engastado', 'Balanco'], 'Biapoiado')
        erow(f, "Vao L (m)", 'L', 10.0)

        # ── Materiais ──
        f = lf("Materiais")
        erow(f, "fck (MPa)",            'fck',   50)
        erow(f, "fckj – transf. (MPa)", 'fckj',  30)
        steel_opts = [f"CP-190 RB {d:.1f}mm"
                      for d in sorted(CP_190_RB_CATALOG.keys())]
        crow(f, "Cabo protendido", 'steel', steel_opts, 'CP-190 RB 15.2mm')
        erow(f, "Cobrimento c (m)", 'cover', 0.04)

        # ── Cargas ──
        f = lf("Carregamentos")
        erow(f, "gk – perm. adic. (kN/m)", 'gk', 20.0)
        erow(f, "qk – variavel  (kN/m)",   'qk', 25.0)
        crow(f, "Uso / destino", 'usage',
             list(PSI.keys()), 'comercial')

        # ── Protensao ──
        f = lf("Protensao")
        erow(f, "Pj – forca total (kN)",  'Pj',      1450.0)
        erow(f, "e – excentr. (m)",        'e',        0.39)
        crow(f, "Nivel de protensao", 'level',
             ['completa', 'limitada', 'parcial'], 'completa')
        erow(f, "Fator Pt/Pj (transf.)", 'ft', 0.90)
        erow(f, "Fator Ps/Pj (servico)", 'fs', 0.75)

        # ── Botao ──
        btn_frame = ttk.Frame(inner)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="  CALCULAR  ",
                   command=self._calculate).pack(fill=tk.X, ipady=6)

    # ── painel de resultados ──────────────────────────────────────────────────

    def _build_results(self, parent):
        self.nb = ttk.Notebook(parent)
        self.nb.pack(fill=tk.BOTH, expand=True)

        # --- Aba 0: Resumo textual
        t0 = ttk.Frame(self.nb)
        self.nb.add(t0, text='  Resumo  ')
        self.txt = tk.Text(t0, font=('Consolas', 10), wrap='none',
                           state='disabled', bg='#fafafa', relief='flat')
        sb0 = ttk.Scrollbar(t0, command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb0.set)
        sb0.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # --- Aba 1: Diagramas M e V
        t1 = ttk.Frame(self.nb)
        self.nb.add(t1, text='  Momentos e Cortantes  ')
        self.fig_mv = Figure(figsize=(10, 8), dpi=95)
        self.cv_mv  = FigureCanvasTkAgg(self.fig_mv, t1)
        NavigationToolbar2Tk(self.cv_mv, t1).pack(side=tk.BOTTOM, fill=tk.X)
        self.cv_mv.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Aba 2: Tensoes nas fibras
        t2 = ttk.Frame(self.nb)
        self.nb.add(t2, text='  Tensoes nas Fibras  ')
        self.fig_st = Figure(figsize=(10, 7), dpi=95)
        self.cv_st  = FigureCanvasTkAgg(self.fig_st, t2)
        NavigationToolbar2Tk(self.cv_st, t2).pack(side=tk.BOTTOM, fill=tk.X)
        self.cv_st.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Aba 3: Secao transversal + checks
        t3 = ttk.Frame(self.nb)
        self.nb.add(t3, text='  Secao e Verificacoes  ')
        self.fig_sc = Figure(figsize=(10, 8), dpi=95)
        self.cv_sc  = FigureCanvasTkAgg(self.fig_sc, t3)
        NavigationToolbar2Tk(self.cv_sc, t3).pack(side=tk.BOTTOM, fill=tk.X)
        self.cv_sc.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ── calculo ───────────────────────────────────────────────────────────────

    def _fv(self, key):
        try:
            return float(self.v[key].get())
        except ValueError:
            raise ValueError(f"Valor invalido no campo '{key}'")

    def _calculate(self):
        try:
            self._run()
        except Exception as exc:
            messagebox.showerror("Erro", str(exc))

    def _run(self):
        # ── leitura ──
        b       = self._fv('b')
        h       = self._fv('h')
        L       = self._fv('L')
        fck     = self._fv('fck')
        fckj    = self._fv('fckj')
        gk      = self._fv('gk')
        qk      = self._fv('qk')
        Pj      = self._fv('Pj')
        e       = self._fv('e')
        ft      = self._fv('ft')
        fs      = self._fv('fs')
        cover   = self._fv('cover')
        sup_nm  = self.v['support'].get()
        usage   = self.v['usage'].get()
        level   = self.v['level'].get()
        st_lbl  = self.v['steel'].get()
        diam    = float(st_lbl.split()[-1].replace('mm', ''))

        # ── objetos ──
        sec  = RectangularSection(b, h)
        conc = Concrete(fck, fckj)
        stl  = PrestressSteel('CP-190 RB', diam)
        lds  = Loads(gk, qk, usage)

        sup_map = {
            'Biapoiado':            ('simply',     SimplySupported(L)),
            'Engastado-Engastado':  ('fixed',      FixedFixed(L)),
            'Balanco':              ('cantilever', Cantilever(L)),
        }
        sup_key, sup = sup_map[sup_nm]

        # ── cargas ──
        sw      = lds.self_weight(sec)          # kN/m
        q_sw    = sw
        q_gk    = sw + gk
        q_total = sw + gk + qk

        # ── arrays de momento ──
        x       = np.linspace(0, L, N)
        M_sw    = np.array([sup.M_uniform(xi, q_sw)    for xi in x])
        M_gk    = np.array([sup.M_uniform(xi, q_gk)    for xi in x])
        M_qk    = np.array([sup.M_uniform(xi, qk)      for xi in x])
        M_se    = np.array([sup.M_uniform(xi, q_total) for xi in x])

        # ── arrays de cortante ──
        V_sw    = _shear(x, M_sw)
        V_gk    = _shear(x, M_gk)
        V_se    = _shear(x, M_se)

        # ── secao critica ──
        crits   = sup.critical_sections()
        xc, _   = crits[0]
        Msw_c   = sup.M_uniform(xc, q_sw)
        Mgk_c   = sup.M_uniform(xc, q_gk)
        Mqk_c   = sup.M_uniform(xc, qk)
        Mse_c   = sup.M_uniform(xc, q_total)

        # ── forcas de protensao ──
        Pt = ft * Pj
        Ps = fs * Pj

        # ── limites e verificacao de tensoes ──
        lims    = stress_limits(conc)
        stt_c   = stresses_at_section(Pt, e, Msw_c, sec)
        sts_c   = stresses_at_section(Ps, e, Mse_c, sec)
        res_t   = check_stresses(*stt_c, lims, 'transfer')
        res_s   = check_stresses(*sts_c, lims, 'service')

        # tensoes ao longo do vao
        stt_arr = np.array([stresses_at_section(Pt, e, M, sec) for M in M_sw])
        sts_arr = np.array([stresses_at_section(Ps, e, M, sec) for M in M_se])

        # ── ELU ──
        dp      = h - cover - diam / 2000
        n_strs  = max(1, int(np.ceil(Pj / stl.Pj_lim_unit())))
        Aps_tot = n_strs * stl.Aps_unit
        MRd     = MRd_simplified(dp, Aps_tot, stl.fpd)
        Mlim    = Mlim_rectangular(b, dp, conc.fcd)
        Md      = Md_ULS(Mgk_c, Mqk_c)

        # ── combinacoes ELS ──
        p1, p2  = PSI[usage]['psi1'], PSI[usage]['psi2']
        combos  = combine_actions(level, Mgk_c, Mqk_c, p1, p2)

        # ── resumo textual ──
        ok = lambda b: "OK   " if b else "FALHA"
        lines = [
            "=" * 64,
            "   VIGA PROTENDIDA  –  NBR 6118:2014 / Torii (2020)",
            "=" * 64,
            "",
            f"  Seccao          b = {b:.3f} m  |  h = {h:.3f} m",
            f"  Area            A = {sec.A:.4f} m2",
            f"  Inercia         I = {sec.I:.4e} m4",
            f"  Modulo secc.    z = {sec.zt:.4e} m3",
            "",
            f"  Concreto        fck = {fck:.0f} MPa  |  fckj = {fckj:.0f} MPa",
            f"                  Ecs = {conc.Ecs()/1000:.2f} GPa  |  fct_m = {conc.fct_m:.3f} MPa",
            "",
            f"  Cabo            {st_lbl}",
            f"                  Aps/cabo = {stl.Aps_unit_mm2:.1f} mm2  |  fpd = {stl.fpd:.2f} MPa",
            f"                  Pj_lim/cabo = {stl.Pj_lim_unit():.2f} kN  |  n_cabos = {n_strs}",
            "",
            f"  Apoio           {sup_nm}  |  L = {L:.2f} m",
            f"  Cargas          sw = {sw:.2f}  gk = {gk:.2f}  qk = {qk:.2f} kN/m",
            "",
            f"  MOMENTOS NA SECCAO CRITICA  (x = {xc:.3f} m)",
            f"    Msw   = {Msw_c:>10.3f} kN.m",
            f"    Mgk   = {Mgk_c:>10.3f} kN.m  (pp + gk)",
            f"    Mqk   = {Mqk_c:>10.3f} kN.m",
            f"    Mse   = {Mse_c:>10.3f} kN.m  (combinacao rara)",
            f"    Md    = {Md:>10.3f} kN.m  (ELU)",
        ]
        for k, v in combos.items():
            lines.append(f"    {k:6s} = {v:>10.3f} kN.m  (ELS)")
        lines += [
            "",
            f"  LIMITES DE TENSAO (MPa)",
            f"    Transferencia   ftt = +{lims.ftt:.3f}  |  ftc = {lims.ftc:.3f}",
            f"    Servico         fst = +{lims.fst:.3f}  |  fsc = {lims.fsc:.3f}",
            "",
            f"  PROTENSAO  Pj = {Pj:.1f} kN  |  e = {e:.4f} m",
            f"    Pt = {Pt:.1f} kN  ({ft:.2f}.Pj)  |  Ps = {Ps:.1f} kN  ({fs:.2f}.Pj)",
            "",
            "  ATO DA PROTENSAO",
            f"    s_top = {stt_c[0]:+.4f} MPa   [{ok(res_t.passes_top)}]"
            f"    (lim: {lims.ftc:.2f} ... +{lims.ftt:.2f})",
            f"    s_bot = {stt_c[1]:+.4f} MPa   [{ok(res_t.passes_bottom)}]",
            "",
            "  EM SERVICO (combinacao rara)",
            f"    s_top = {sts_c[0]:+.4f} MPa   [{ok(res_s.passes_top)}]"
            f"    (lim: {lims.fsc:.2f} ... +{lims.fst:.2f})",
            f"    s_bot = {sts_c[1]:+.4f} MPa   [{ok(res_s.passes_bottom)}]",
            "",
            f"  ELU – FLEXAO",
            f"    dp   = {dp:.4f} m  |  Aps = {Aps_tot*1e6:.2f} mm2",
            f"    MRd  = {MRd:>10.3f} kN.m",
            f"    Mlim = {Mlim:>10.3f} kN.m  (limite de ductilidade)",
            f"    Md   = {abs(Md):>10.3f} kN.m",
            f"    MRd >= Md   [{ok(MRd >= abs(Md))}]",
            f"    MRd >= Mlim [{ok(MRd >= Mlim)}]",
            "=" * 64,
        ]

        self.txt.configure(state='normal')
        self.txt.delete('1.0', tk.END)
        self.txt.insert('1.0', '\n'.join(lines))
        self.txt.configure(state='disabled')

        # ── graficos ──
        self._plot_mv(x, M_sw, M_gk, M_se, V_sw, V_gk, V_se,
                      L, sw, gk, qk, b, h, sup_nm, sup_key)
        self._plot_stresses(x, stt_arr, sts_arr, lims)
        self._plot_section(sec, e, cover, diam, n_strs,
                           MRd, Mlim, Md, stt_c, sts_c, lims)

        self.nb.select(1)

    # ─────────────────────────────────────────────────────────────────────────
    #  GRAFICO 1: Diagramas de Momentos e Cortantes
    # ─────────────────────────────────────────────────────────────────────────

    def _plot_mv(self, x, M_sw, M_gk, M_se, V_sw, V_gk, V_se,
                 L, sw, gk, qk, b, h, sup_nm, sup_key):
        fig = self.fig_mv
        fig.clear()
        fig.patch.set_facecolor('#f8f8f8')
        gs = GridSpec(3, 1, figure=fig, hspace=0.55,
                      top=0.96, bottom=0.07, left=0.09, right=0.97,
                      height_ratios=[1.2, 2, 2])

        # ── esquema ──
        ax0 = fig.add_subplot(gs[0])
        self._beam_schema(ax0, L, b, h, sw + gk + qk, sup_nm)

        # ── momentos ──
        ax1 = fig.add_subplot(gs[1])
        ax1.axhline(0, color='black', lw=0.8)
        ax1.plot(x, M_sw,  '--', color='#888', lw=1.2, label=f'pp  ({sw:.2f} kN/m)')
        ax1.plot(x, M_gk,  '-.',  color='#2980b9', lw=1.5,
                 label=f'pp+gk  ({sw+gk:.2f} kN/m)')
        ax1.plot(x, M_se,  '-',  color='#c0392b', lw=2.2,
                 label=f'total  ({sw+gk+qk:.2f} kN/m)')
        ax1.fill_between(x, M_se, 0, alpha=0.10, color='#c0392b')

        # anotacao do maximo
        imax = int(np.argmax(np.abs(M_se)))
        mx, my = x[imax], M_se[imax]
        off = my * 0.15 if my != 0 else 20
        ax1.annotate(f'{my:.1f} kN.m',
                     xy=(mx, my), xytext=(mx + L * 0.04, my - off),
                     fontsize=8, color='#c0392b',
                     arrowprops=dict(arrowstyle='->', color='#c0392b', lw=0.8))

        ax1.set_xlabel('x (m)', fontsize=9)
        ax1.set_ylabel('M (kN.m)', fontsize=9)
        ax1.set_title('Diagrama de Momentos Fletores', fontsize=10, fontweight='bold')
        ax1.legend(fontsize=8, loc='best')
        ax1.grid(True, alpha=0.25, linestyle='--')
        ax1.set_xlim(0, L)

        # ── cortantes ──
        ax2 = fig.add_subplot(gs[2])
        ax2.axhline(0, color='black', lw=0.8)
        ax2.plot(x, V_sw,  '--', color='#888', lw=1.2, label='Vpp')
        ax2.plot(x, V_gk,  '-.',  color='#2980b9', lw=1.5, label='Vpp+gk')
        ax2.plot(x, V_se,  '-',  color='#e67e22', lw=2.2, label='Vtotal')
        ax2.fill_between(x, V_se, 0, where=(V_se >= 0),
                         alpha=0.12, color='#e67e22')
        ax2.fill_between(x, V_se, 0, where=(V_se < 0),
                         alpha=0.12, color='#9b59b6')

        # valores nos extremos
        for xi, vi in [(x[0], V_se[0]), (x[-1], V_se[-1])]:
            ax2.annotate(f'{vi:.1f} kN',
                         xy=(xi, vi), xytext=(xi + L * 0.04, vi * 0.8 + 1e-9),
                         fontsize=8, color='#e67e22',
                         arrowprops=dict(arrowstyle='->', color='#e67e22', lw=0.8))

        ax2.set_xlabel('x (m)', fontsize=9)
        ax2.set_ylabel('V (kN)', fontsize=9)
        ax2.set_title('Diagrama de Forca Cortante', fontsize=10, fontweight='bold')
        ax2.legend(fontsize=8, loc='best')
        ax2.grid(True, alpha=0.25, linestyle='--')
        ax2.set_xlim(0, L)

        self.cv_mv.draw()

    def _beam_schema(self, ax, L, b, h, q, sup_nm):
        ax.set_xlim(-L * 0.07, L * 1.07)
        ax.set_ylim(-0.65, 2.1)
        ax.axis('off')
        ax.set_title('Esquema da Viga', fontsize=9, fontweight='bold')

        bh = 0.45  # altura do retangulo esquematico
        rect = Rectangle((0, 0), L, bh,
                          facecolor='#d6e4f0', edgecolor='#2980b9', lw=1.8, zorder=2)
        ax.add_patch(rect)

        # setas de carga
        nq = 12
        xs = np.linspace(L * 0.04, L * 0.96, nq)
        for xi in xs:
            ax.annotate('', xy=(xi, bh), xytext=(xi, bh + 0.55),
                        arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.1))
        ax.plot([xs[0], xs[-1]], [bh + 0.55, bh + 0.55], color='#c0392b', lw=1.5)
        ax.text(L / 2, bh + 0.75, f'q = {q:.2f} kN/m',
                ha='center', va='bottom', fontsize=9,
                color='#c0392b', fontweight='bold')

        # cota
        ax.annotate('', xy=(L, -0.35), xytext=(0, -0.35),
                    arrowprops=dict(arrowstyle='<->', color='#444', lw=1.0))
        ax.text(L / 2, -0.52, f'L = {L:.2f} m', ha='center', fontsize=9, color='#333')

        # apoios
        if 'Biapoiado' in sup_nm:
            for xp in [0, L]:
                s = L * 0.025
                ax.plot([xp - s, xp + s, xp, xp - s],
                        [-0.02, -0.02, 0, -0.02], color='#555', lw=1.4)
                ax.plot([xp - s * 1.4, xp + s * 1.4], [-0.06, -0.06],
                        color='#555', lw=1.4)
        elif 'Engastado' in sup_nm:
            for xp, dx in [(0, -1), (L, 1)]:
                ax.fill_betweenx([0, bh],
                                  xp, xp + dx * L * 0.03,
                                  color='#777', alpha=0.8, zorder=1)
        elif 'Balanco' in sup_nm:
            ax.fill_betweenx([0, bh], 0, -L * 0.03,
                              color='#777', alpha=0.8, zorder=1)

        # rotulo secao
        ax.text(L * 0.02, bh / 2,
                f'b x h = {b*100:.0f} x {h*100:.0f} cm',
                va='center', fontsize=8, color='#2980b9')

    # ─────────────────────────────────────────────────────────────────────────
    #  GRAFICO 2: Tensoes nas fibras
    # ─────────────────────────────────────────────────────────────────────────

    def _plot_stresses(self, x, stt_arr, sts_arr, lims):
        fig = self.fig_st
        fig.clear()
        fig.patch.set_facecolor('#f8f8f8')
        gs = GridSpec(2, 1, figure=fig, hspace=0.50,
                      top=0.94, bottom=0.08, left=0.09, right=0.97)

        data = [
            (stt_arr, 'Ato da Protensao   (Pt, Msw)', lims.ftt, lims.ftc),
            (sts_arr, 'Em Servico   (Ps, Mse rara)',   lims.fst, lims.fsc),
        ]
        for idx, (arr, title, flim_t, flim_c) in enumerate(data):
            ax = fig.add_subplot(gs[idx])
            top, bot = arr[:, 0], arr[:, 1]

            ax.axhline(0, color='black', lw=0.8)
            ax.plot(x, top, '-',  color='#2980b9', lw=2.0, label='Fibra superior')
            ax.plot(x, bot, '--', color='#e67e22', lw=2.0, label='Fibra inferior')

            ax.axhline(flim_t, color='#27ae60', ls=':', lw=1.5,
                       label=f'Lim. tracao = +{flim_t:.2f} MPa')
            ax.axhline(flim_c, color='#e74c3c', ls=':', lw=1.5,
                       label=f'Lim. compressao = {flim_c:.2f} MPa')
            ax.fill_between(x, flim_c, flim_t,
                            alpha=0.06, color='#27ae60', label='Faixa admissivel')

            # destaca violacoes
            for sig in [top, bot]:
                ax.fill_between(x, sig, flim_t,
                                where=(sig > flim_t), alpha=0.25, color='#e74c3c',
                                label='Violacao' if idx == 0 and np.any(sig > flim_t) else '')
                ax.fill_between(x, sig, flim_c,
                                where=(sig < flim_c), alpha=0.25, color='#e74c3c')

            # anotacoes max/min
            for sig, cor, pos in [(top, '#2980b9', 0.97), (bot, '#e67e22', 0.03)]:
                ival = int(np.argmax(np.abs(sig)))
                ax.annotate(f'{sig[ival]:+.2f} MPa',
                            xy=(x[ival], sig[ival]),
                            xytext=(x[ival] + (x[-1] - x[0]) * 0.04,
                                    sig[ival] * 0.85 + 1e-9),
                            fontsize=8, color=cor,
                            arrowprops=dict(arrowstyle='->', color=cor, lw=0.7))

            ax.set_xlabel('x (m)', fontsize=9)
            ax.set_ylabel('Tensao (MPa)', fontsize=9)
            ax.set_title(title, fontsize=10, fontweight='bold')
            ax.legend(fontsize=8, ncol=2, loc='lower center')
            ax.grid(True, alpha=0.25, linestyle='--')
            ax.set_xlim(x[0], x[-1])

        self.cv_st.draw()

    # ─────────────────────────────────────────────────────────────────────────
    #  GRAFICO 3: Secao transversal + verificacoes
    # ─────────────────────────────────────────────────────────────────────────

    def _plot_section(self, sec, e, cover, diam_mm, n_strs,
                      MRd, Mlim, Md, stt_c, sts_c, lims):
        fig = self.fig_sc
        fig.clear()
        fig.patch.set_facecolor('#f8f8f8')
        gs = GridSpec(2, 2, figure=fig, hspace=0.50, wspace=0.38,
                      top=0.94, bottom=0.07, left=0.08, right=0.97)

        # ── desenho da secao (coluna esquerda, 2 linhas) ──
        ax0 = fig.add_subplot(gs[:, 0])
        self._draw_cross_section(ax0, sec, e, cover, diam_mm, n_strs)

        # ── grafico de barras: tensoes na secao critica ──
        ax1 = fig.add_subplot(gs[0, 1])
        cats  = ['stop\n(transf.)', 'sbot\n(transf.)', 'stop\n(servico)', 'sbot\n(servico)']
        vals  = [stt_c[0], stt_c[1], sts_c[0], sts_c[1]]
        lim_pairs = [(lims.ftc, lims.ftt)] * 2 + [(lims.fsc, lims.fst)] * 2
        clrs  = ['#27ae60' if lo <= v <= hi else '#e74c3c'
                 for v, (lo, hi) in zip(vals, lim_pairs)]
        bars  = ax1.bar(cats, vals, color=clrs, edgecolor='black', lw=0.5, alpha=0.85)
        for bar, v in zip(bars, vals):
            va = 'bottom' if v >= 0 else 'top'
            ax1.text(bar.get_x() + bar.get_width() / 2, v,
                     f'{v:+.2f}', ha='center', va=va, fontsize=8, fontweight='bold')
        ax1.axhline(lims.ftt, color='#27ae60', ls=':', lw=1.2, label=f'ftt={lims.ftt:.2f}')
        ax1.axhline(lims.ftc, color='#e74c3c', ls=':', lw=1.2, label=f'ftc={lims.ftc:.2f}')
        ax1.axhline(lims.fst, color='#27ae60', ls='--', lw=1.0, label=f'fst={lims.fst:.2f}')
        ax1.axhline(lims.fsc, color='#e74c3c', ls='--', lw=1.0, label=f'fsc={lims.fsc:.2f}')
        ax1.axhline(0, color='black', lw=0.6)
        ax1.set_ylabel('Tensao (MPa)', fontsize=9)
        ax1.set_title('Tensoes na Seccao Critica', fontsize=10, fontweight='bold')
        ax1.legend(fontsize=7, ncol=2)
        ax1.grid(True, axis='y', alpha=0.25, linestyle='--')

        # ── grafico de barras: verificacao ELU ──
        ax2 = fig.add_subplot(gs[1, 1])
        uls_lbl = ['MRd\n(resist.)', 'Mlim\n(ductil.)', '|Md|\n(ELU)']
        uls_val = [MRd, Mlim, abs(Md)]
        uls_clr = ['#2980b9', '#8e44ad', '#e74c3c']
        bars2   = ax2.bar(uls_lbl, uls_val,
                          color=uls_clr, edgecolor='black', lw=0.5, alpha=0.85)
        for bar, v in zip(bars2, uls_val):
            ax2.text(bar.get_x() + bar.get_width() / 2, v,
                     f'{v:.1f}', ha='center', va='bottom',
                     fontsize=9, fontweight='bold')
        # linha MRd para referencia
        ax2.axhline(MRd, color='#2980b9', ls='--', lw=1.0, alpha=0.6)
        ax2.set_ylabel('Momento (kN.m)', fontsize=9)
        ax2.set_title('Verificacao ELU - Flexao', fontsize=10, fontweight='bold')
        ax2.grid(True, axis='y', alpha=0.25, linestyle='--')

        # status ELU
        status = "OK" if MRd >= abs(Md) else "FALHA"
        clr_s  = '#27ae60' if MRd >= abs(Md) else '#e74c3c'
        ax2.text(0.98, 0.96, f'MRd >= Md: {status}',
                 transform=ax2.transAxes, ha='right', va='top',
                 fontsize=9, fontweight='bold', color=clr_s,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor=clr_s, alpha=0.9))

        self.cv_sc.draw()

    def _draw_cross_section(self, ax, sec, e, cover, diam_mm, n_strs):
        b_cm   = sec.b * 100
        h_cm   = sec.h * 100
        d_cm   = diam_mm / 10
        r_cm   = d_cm / 2

        # contorno
        rect = Rectangle((0, 0), b_cm, h_cm,
                          facecolor='#d6e4f0', edgecolor='#2980b9', lw=2, zorder=1)
        ax.add_patch(rect)

        # centroide
        yg = h_cm / 2
        ax.axhline(yg, color='#555', ls='--', lw=1.0, label=f'centroide ({yg:.0f} cm)')

        # linha do cabo (e)
        y_e = (sec.h / 2 - e) * 100
        ax.axhline(y_e, color='#c0392b', ls='-.', lw=1.3,
                   label=f'cabo design  e={e:.3f} m  (y={y_e:.1f} cm)')

        # cordoalhas fisicas
        c_cm    = cover * 100
        spc_cm  = d_cm + 1.5
        avail_w = b_cm - 2 * c_cm - 2 * r_cm
        n_row   = max(1, int(avail_w // (d_cm + 1.5)) + 1)
        colors  = ['#c0392b', '#922b21', '#7b241c']
        placed  = 0
        row_i   = 0
        while placed < n_strs:
            n_this = min(n_row, n_strs - placed)
            xs_s   = np.linspace(c_cm + r_cm,
                                 b_cm - c_cm - r_cm, max(1, n_this))
            y_s    = c_cm + r_cm + row_i * spc_cm
            for xi in xs_s:
                ax.add_patch(Circle((xi, y_s), r_cm,
                                    facecolor=colors[min(row_i, 2)],
                                    edgecolor='black', lw=0.5, zorder=5))
            placed += n_this
            row_i  += 1

        # cotas
        ax.annotate('', xy=(b_cm + 4, 0), xytext=(b_cm + 4, h_cm),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1.0))
        ax.text(b_cm + 7, h_cm / 2,
                f'h={sec.h*100:.0f} cm', va='center', fontsize=8, rotation=90)

        ax.annotate('', xy=(0, -4), xytext=(b_cm, -4),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1.0))
        ax.text(b_cm / 2, -7.5,
                f'b={sec.b*100:.0f} cm', ha='center', fontsize=8)

        ax.set_xlim(-6, b_cm + 18)
        ax.set_ylim(-14, h_cm + 10)
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlabel('cm', fontsize=8)
        ax.set_ylabel('cm', fontsize=8)
        ax.set_title(
            f'Seccao Transversal\n{n_strs} cabo(s)  CP-190 RB {diam_mm:.1f} mm',
            fontsize=9, fontweight='bold')
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(True, alpha=0.15)


if __name__ == '__main__':
    app = BeamApp()
    app.mainloop()
