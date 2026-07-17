# Règles de Design de l'Espace de Travail - DEKOUWAY

## DESIGN PHILOSOPHY

DEKOUWAY est une plateforme immobilière premium.

Chaque écran doit inspirer :
- la confiance
- la sécurité
- la simplicité
- la rapidité
- le professionnalisme

Le design doit sembler conçu par une équipe Senior UX de Airbnb.
Chaque composant doit avoir une raison d'exister.
Aucun élément décoratif inutile.
Le contenu est prioritaire sur les effets visuels.
Le design doit être intemporel.
L'objectif n'est pas d'impressionner.
L'objectif est de rassurer l'utilisateur.


## DESIGN RULES

Toujours appliquer :
- Beaucoup d'espace blanc.
- Hiérarchie visuelle claire.
- Grille 8px.
- Alignements parfaits.
- Padding cohérents.
- Margins cohérentes.
- Couleurs limitées.
- Peu de texte.
- Icônes simples.
- Photos de qualité.
- Cartes aérées.
- Navigation évidente.

Le regard de l'utilisateur doit naturellement suivre :
1. Header
2. ↓ Recherche
3. ↓ Filtres
4. ↓ Résultats
5. ↓ Call To Action


## COMPONENT FIRST

Ne jamais coder une page directement.
Toujours suivre cet ordre :
1. Créer le composant
2. Tester le composant
3. Valider le responsive
4. Documenter le composant
5. Réutiliser le composant

Une page ne doit contenir que des composants.
Aucun HTML dupliqué.
Tous les composants doivent pouvoir être réutilisés dans plusieurs pages.


## MOBILE FIRST

Commencer TOUJOURS par le design mobile.
Ensuite :
1. Tablet
2. Laptop
3. Desktop

Jamais l'inverse. Le mobile est la version de référence.


## TAILWIND

Utiliser uniquement TailwindCSS.
Ne jamais écrire : `style="..."` ou de CSS inline.
Créer des composants Tailwind propres.
Respecter les conventions officielles TailwindCSS v4.


## ACCESSIBILITÉ

Toutes les pages doivent respecter WCAG AA.
Ajouter :
- `aria-label`
- `aria-current`
- `aria-expanded`
- `role`
- `focus-visible`

Contraste supérieur à 4.5.
Tous les boutons doivent être navigables au clavier.
Tous les formulaires doivent être accessibles.


## PERFORMANCE

Optimiser systématiquement :
- Images
- SVG
- HTML
- CSS
- Javascript
- Lazy Loading
- Responsive Images

Aucune librairie inutile.
Objectif Lighthouse :
- Performance ≥ 95
- Accessibility ≥ 95
- Best Practices ≥ 95
- SEO ≥ 95


## DJANGO

Respecter les bonnes pratiques Django.
Toujours utiliser :
- `{% extends %}`
- `{% include %}`
- `{% block %}`

Ne jamais dupliquer un layout.
Créer des layouts :
- `public.html`
- `auth.html`
- `dashboard.html`

Tous les composants doivent être découplés.


## STRUCTURE

Respecter cette architecture :
```
templates/
  components/
  layouts/
  pages/
```
Chaque composant doit avoir son propre fichier.
Chaque écran doit avoir son propre fichier.
Aucun fichier supérieur à 300 lignes.
Si un fichier dépasse 300 lignes, le découper automatiquement.


## AUTO REVIEW

Après chaque écran terminé :
Faire une revue complète et vérifier :
- Responsive
- Accessibilité
- Couleurs
- Espacements
- Alignements
- Performance
- Réutilisabilité
- Pixel Perfect

Si une anomalie existe, la corriger, puis refaire une nouvelle revue.
Continuer jusqu'à ne plus détecter aucune anomalie.
Ne jamais passer à l'écran suivant avant validation complète.


## INTERDICTIONS

Interdiction absolue de :
- Bootstrap, Material UI, Flowbite, DaisyUI
- CSS inline, Javascript inline
- Composants copiés, code dupliqué
- Magic Numbers
- Couleurs aléatoires, fonts aléatoires
- Animations excessives, gradients, glassmorphism, neumorphism, effets 3D, ombres fortes, bordures épaisses
- Design fantaisiste

Le rendu doit être sobre, professionnel et cohérent.


## DEFINITION OF DONE

Le travail est terminé uniquement lorsque :
✓ Le rendu est identique à la maquette.
✓ Responsive parfait.
✓ Pixel Perfect.
✓ Tous les composants sont réutilisables.
✓ Aucun composant dupliqué.
✓ Aucun warning HTML.
✓ Aucun warning Tailwind.
✓ Structure Django propre.
✓ Mobile First respecté.
✓ Design premium.
✓ Code maintenable.
✓ Score Lighthouse supérieur à 95.
✓ Conforme aux standards Airbnb, Booking et Stripe.


## MODE D'EXÉCUTION

Tu ne dois jamais générer plusieurs écrans simultanément.
Tu travailles par itérations.
Pour chaque écran :
1. Créer les composants nécessaires.
2. Implémenter l'écran.
3. Vérifier la conformité avec la maquette.
4. Corriger les écarts.
5. Optimiser le code.
6. Valider le responsive.
7. Attendre la validation avant de passer à l'écran suivant.

Ne saute jamais d'étape.
