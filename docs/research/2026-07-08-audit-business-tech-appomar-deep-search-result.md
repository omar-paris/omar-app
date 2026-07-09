# **Rapport d'Analyse Comparative et d'Enrichissement de l'Audit Business & Tech pour AppOmar**

## **1\. Executive Summary en 10 Points Clés**

La transformation numérique des très petites entreprises (TPE) et petites et moyennes entreprises (PME) françaises s'accélère sous la pression conjointe des évolutions réglementaires et de la nécessité d'optimiser l'efficacité opérationnelle1. Le présent rapport propose une refonte méthodologique de l'audit conversationnel intégré au produit AppOmar.

1. **Hybridation des données d'audit** : L'efficacité d'un diagnostic technologique repose sur la confrontation systématique entre les déclarations spontanées du dirigeant et l'analyse automatisée de son empreinte publique (API SIRENE3, sites web1, fiches Google Business Profile4).
2. **Adoption asymétrique de l'intelligence artificielle** : L'usage de l'IA a doublé en un an pour atteindre 26 % des TPE/PME françaises en 20251. Néanmoins, l'adoption demeure périphérique (rédaction, assistance) et peine à s'intégrer dans les processus métiers critiques6.
3. **Barrière structurelle des compétences** : Bien que 55 % des dirigeants déclarent disposer de compétences numériques internes1, le manque de temps représente le premier obstacle à la formation (53 %)1, justifiant le déploiement d'agents IA autonomes pour compenser ce déficit d'encadrement7.
4. **Intensification de la vulnérabilité cyber** : Plus de 52 % des dirigeants de TPE/PME expriment des craintes face aux cyberattaques, et plus d'un tiers a déjà subi un incident1. L'audit doit impérativement évaluer les mesures préventives élémentaires selon les recommandations de l'ANSSI8.
5. **Urgence réglementaire de la facturation électronique** : L'obligation d'émission au format électronique s'appliquera aux TPE/PME dès le 1er septembre 20271. L'intégration d'un diagnostic de préparation à cette réforme constitue un levier d'engagement majeur.
6. **Valorisation méthodologique par l'impact** : En s'inspirant des diagnostics structurés comme le Diag Data IA de Bpifrance10, AppOmar doit orienter ses recommandations vers le retour sur investissement (ROI) opérationnel et la réduction de la charge mentale10.
7. **Souveraineté et conformité RGPD** : Toute réutilisation de données publiques à des fins de profilage ou de prospection commerciale doit respecter les principes stricts de la CNIL en matière d'information préalable et de droit d'opposition pour les professionnels13.
8. **Onboarding IA orienté processus** : Le diagnostic final doit se traduire directement par la génération automatique d'un profil d'agent IA (agent_profile), délimitant strictement ses compétences, ses connecteurs et ses barrières de sécurité.
9. **Devis d'accompagnement non intrusif** : Pour éviter l'effet d'un tunnel de vente agressif, la tarification doit être déduite de manière causale et transparente à partir des recommandations validées par le client, classées selon l'effort de mise en œuvre.
10. **Architecture YAML dynamique** : L'implémentation de l'audit exige un arbre de décision structuré sous forme de fichier YAML exécutable, capable de gérer des branchements conditionnels selon la taille, le secteur et la maturité de l'entreprise.

## **2\. Analyse Comparative des Frameworks d'Audit**

L'optimisation d'un modèle d'audit destiné aux petites structures requiert une synthèse rigoureuse des cadres existants. Le tableau suivant compare les principales méthodologies d'évaluation numérique, de maturité IA et de cybersécurité afin de dégager les meilleures pratiques transposables à un environnement conversationnel.

| Framework | Organisme Promoteur | Dimensions Clés Évaluées | Points Forts pour les TPE/PME | Limites en Contexte Conversationnel Direct |
| :---- | :---- | :---- | :---- | :---- |
| **Baromètre France Num** [source 1, 15] | DGE / Ministère de l'Économie | Perception du numérique, promotion commerciale, gestion et pilotage, usages IA, cybersécurité, dépenses15. | Données statistiques de référence sur l'écosystème français, identification précise des freins opérationnels1. | Approche purement déclarative et statistique, absence de plan d'action personnalisé immédiat. |
| **Diag Data IA** [source 10, 11] | Bpifrance / France 2030 | Potentiel de valorisation des données, cas d'usage IA prioritaires, faisabilité technique, feuille de route opérationnelle10. | Diagnostic de haut niveau étalé sur plusieurs jours, orientation forte vers le retour sur investissement (ROI)10. | Conçu pour des PME structurées (>10 salariés, >1M€ CA), trop lourd et onéreux pour les micro-entreprises10. |
| **SME AI Readiness Framework** [source 18] | OCDE / G7 | Intégration fonctionnelle de l'IA, compétences, infrastructures de connectivité, gouvernance, gestion des risques18. | Segmentation claire des profils (Novice, Optimiseur, Explorateur), questionnements orientés sur la prise de décision humaine7. | Terminologie parfois trop académique pour des artisans ou des commerçants de proximité. |
| **Cyberdépart / MonAideCyber** [source 20, 21] | ANSSI / GIP ACYMA | Gouvernance cyber, accès aux systèmes, sécurité des postes, réseau, sensibilisation, réaction aux attaques9. | Diagnostic rapide (1h30), gratuit, anonyme, débouchant sur 6 mesures prioritaires concrètes21. | Nécessite un tiers de confiance physique (Aidant cyber) et n'est pas adapté aux micro-entreprises solo9. |
| **Guide d'hygiène informatique (ANSSI)** [source 8] | ANSSI | Cartographie du parc, sauvegardes, mises à jour, antivirus, politique de mots de passe, cloisonnement des usages8. | Standard absolu de sécurité numérique, actions concrètes et éprouvées à fort impact préventif8. | Difficilement assimilable de manière autonome par un dirigeant non technique sans intermédiation conversationnelle. |
| **COBIT / ITIL (Simplifié)** | ISACA / AXELOS | Gouvernance IT, gestion du changement, alignement stratégique, gestion de la valeur et des risques. | Rigueur extrême dans la structuration des processus et la traçabilité des d'écisions technologiques. | Trop complexe, requiert une organisation interne structurée et des ressources dédiées inexistantes en TPE. |

L'analyse comparative démontre que l'adaptation de ces cadres exige de traduire des exigences de gouvernance ou de sécurité complexes en questions pratiques, imagées et directement reliées au quotidien de l'artisan ou du commerçant. Plutôt que d'interroger le client sur sa "politique de gestion des risques informationnels selon la norme ISO 27001", l'agent conversationnel posera une question sur la perte d'un téléphone portable professionnel contenant tous les contacts et l'accès aux comptes bancaires de l'entreprise. De même, l'évaluation de la maturité IA inspirée des critères de l'OCDE ne se focalisera pas sur l'existence d'une infrastructure de calcul distribué18, mais sur l'utilisation concrète d'assistants rédactionnels ou de fonctionnalités intelligentes embarquées dans les logiciels de gestion commerciale existants6.

## **3\. Architecture d'Audit Recommandée et Trajectoire de Livraison (V0 / V1 / V2)**

Afin de maximiser l'engagement du dirigeant de TPE/PME tout en garantissant la rigueur scientifique du diagnostic, une architecture d'audit hybride en trois niveaux est préconisée. Ce parcours est conçu pour durer entre 20 et 30 minutes lors de la session initiale, avec des options d'approfondissement asynchrones.
Le tableau ci-dessous cartographie la répartition des dimensions d'audit à travers les différentes phases de livraison du produit AppOmar.

| Dimension d'Audit | Niveau d'Intégration | Justification Méthodologique | Indicateurs Cibles |
| :---- | :---- | :---- | :---- |
| **Identité & Contexte Officiel** | **V0 (Socle Initial)** | Validation de l'existence légale de l'entreprise et réduction de l'effort de saisie initiale3. | Raison sociale, code NAF, effectifs, adresse administrative3. |
| **Modèle Économique & Proposition de Valeur** | **V0 (Socle Initial)** | Compréhension immédiate de la structure de revenus et des flux commerciaux16. | Typologie de clientèle (B2B/B2C), saisonnalité, complexité de l'offre. |
| **Semaine Réelle & Charge Mentale** | **V0 (Socle Initial)** | Identification des inefficacités opérationnelles majeures et des sources de fatigue émotionnelle12. | Temps perdu sur tâches répétitives, processus chronophages12. |
| **Hygiène Cyber Minimale** | **V0 (Socle Initial)** | Évaluation du niveau d'exposition aux menaces cyber critiques selon les normes d'hygiène6. | Politique de sauvegarde (3-2-1), gestion des accès et des mots de passe8. |
| **Maturité Numérique & IA Subjective** | **V0 (Socle Initial)** | Évaluation de l'appétence technologique globale et identification des outils en place2. | Outils de communication, logiciels de gestion existants, usages IA de base6. |
| **Parcours Client & Acquisition** | **V1 (Enrichissement)** | Analyse de l'entonnoir de conversion et de la visibilité sur les réseaux d'acquisition1. | Fiche Google Business Profile4, site internet, formulaires de contact1. |
| **Gestion administrative & Finance** | **V1 (Enrichissement)** | Évaluation de la chaîne de facturation et niveau de préparation à la transition réglementaire de 20271. | Processus d'émission de devis, facturation, relance d'impayés, outils comptables26. |
| **Équipe & Organisation RH** | **V2 (Approfondi)** | Analyse des plannings, de la transmission des consignes et de l'encadrement des collaborateurs25. | Gestion des plannings d'équipes (Skello/Combo)25, partage des accès informatiques8. |
| **Maturité Data & IA Objective** | **V2 (Approfondi)** | Audit de la qualité des données internes et faisabilité d'intégration d'un agent IA spécialisé2. | Structure des fichiers clients, conformité RGPD, APIs disponibles pour l'automatisation2. |

La trajectoire de livraison proposée permet d'assurer une expérience utilisateur fluide en V0 en évitant l'épuisement cognitif lié à des questions d'infrastructure trop lourdes. Les dimensions plus complexes (V1 et V2) sont introduites de manière asynchrone ou déléguées à l'agent conversationnel d'accompagnement une fois la confiance établie.

## **4\. Banque Complète de Questions Conversationnelles par Étape**

Pour préserver l'expérience premium d'AppOmar, chaque question posée par l'agent doit être courte, humaine et dénuée de jargon technique. Les 14 étapes de l'arbre d'audit sont déclinées ci-dessous avec leurs spécifications fonctionnelles et techniques.

### **Étape 1 : pacte**

* **Formulation d'Omar** : *"Bonjour. Je suis ravi de faire votre connaissance. Mon but aujourd'hui n'est pas de vous faire remplir un formulaire austère de plus, mais de comprendre la réalité de votre quotidien d'entrepreneur, vos réussites, mais aussi ce qui pèse parfois sur vos semaines. Nous allons poser un diagnostic complet sur votre activité en une vingtaine de minutes. Vous êtes libre de sauter les questions qui vous semblent trop intimes, et nous validerons ensemble chaque étape avant d'envisager la suite. Êtes-vous prêt à démarrer ?"*
* **Justification méthodologique** : Établissement de l'alliance thérapeutique et sécurisation du cadre temporel pour minimiser le taux d'abandon précoce.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Disponibilité temporelle de l'utilisateur, niveau d'engagement immédiat. |
| **Réponses typiques** | "Oui, c'est parti", "Je n'ai pas beaucoup de temps", "Expliquez-moi d'abord comment ça marche". |
| **Relance unique** | *"Pas d'inquiétude, nous pouvons nous concentrer sur l'essentiel en 10 minutes si vous préférez."* |
| **Boutons conseillés** | [Démarrer l'audit (20 min)] ; [Faire le parcours rapide (10 min)] |
| **Champ structuré YAML** | audit.pacte.consent_and_tempo |
| **Impact livrable** | Personnalisation du rythme d'échange et sélection du profil d'audit (complet vs rapide). |

### **Étape 2 : identity_public_context**

* **Formulation d'Omar** : *"Pour commencer sur des bases solides, pourriez-vous simplement m'indiquer le nom de votre entreprise ou votre numéro Siren, ainsi que la ville où vous êtes installé ?"*
* **Justification méthodologique** : Permet de requêter instantanément l'API SIRENE pour valider l'existence légale de la structure et pré-remplir la fiche d'identité d'entreprise3.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Siren de l'entreprise3, raison sociale3, localisation administrative23. |
| **Réponses typiques** | "Siren : 123456789", "Boulangerie de la Gare à Lille"28, "Mon entreprise s'appelle Cabinet Spencer"30. |
| **Relance unique** | *"Je n'ai pas trouvé de correspondance exacte. Pouvez-vous vérifier l'orthographe du nom ou me donner le code postal de votre établissement ?"* |
| **Boutons conseillés** | [Saisir manuellement] ; [Rechercher l'entreprise] |
| **Champ structuré YAML** | audit.identity.public_query |
| **Impact livrable** | Remplissage automatique de la section "Carte d'identité" du rapport final3. |

### **Étape 3 : public_sources_consent**

* **Formulation d'Omar** : *"Pour m'éviter de vous poser trop de questions techniques, m'autorisez-vous à analyser rapidement votre site internet et votre fiche d'établissement en ligne ? Je ferai cela de manière totalement transparente pour vous faire gagner du temps."*
  [source 1, 4]
* **Justification méthodologique** : Assure la conformité réglementaire RGPD concernant la collecte de données publiques issues d'internet à des fins d'évaluation commerciale14.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Accord ou refus explicite par source numérique identifiée. |
| **Réponses typiques** | "Oui, vous pouvez regarder", "D'accord pour le site mais pas Google", "Je n'ai pas de site web"1. |
| **Relance unique** | *"Cette analyse m'aide à cartographier votre visibilité. Si vous préférez, nous pouvons sauter cette étape."* |
| **Boutons conseillés** | [Tout autoriser] ; [Autoriser uniquement le site web]1 ; [Passer sans recherche] |
| **Champ structuré YAML** | audit.consent.sources_opt_in |
| **Impact livrable** | Activation des modules d'enrichissement automatique et de diagnostic de la présence en ligne4. |

### **Étape 4 : activity_business_model**

* **Formulation d'Omar** : *"Comment décririez-vous le cœur de votre activité ? Vendez-vous principalement à des particuliers de votre région ou à d'autres entreprises professionnels ?"*
* **Justification méthodologique** : Détermination de l'orientation stratégique de l'entreprise pour ajuster l'arbre conversationnel vers les thématiques adaptées (B2B vs B2C)7.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Segment de clientèle principal, nature des prestations (physique vs intellectuel), zone de chalandise. |
| **Réponses typiques** | "Je suis électricien pour des particuliers locaux", "Nous sommes un cabinet de conseil B2B en ligne"33. |
| **Relance unique** | *"Votre clientèle est-elle principalement fidèle et régulière, ou devez-vous constamment chercher de nouveaux acheteurs ?"* |
| **Boutons conseillés** | [Particuliers (B2C)]32 ; [Entreprises (B2B)]32 ; [Mixte B2B / B2C] |
| **Champ structuré YAML** | audit.business_model.target_and_offer |
| **Impact livrable** | Structuration de la section "Modèle d'affaires" du rapport final et orientation des algorithmes de recommandation. |

### **Étape 5 : person_and_goals**

* **Formulation d'Omar** : *"En tant que dirigeant, quel est votre objectif principal pour les douze prochains mois ? Souhaitez-vous stabiliser votre organisation pour gagner en sérénité, ou cherchez-vous plutôt à accélérer votre croissance commerciale ?"*
* **Justification méthodologique** : Alignement des recommandations d'automatisation technologique sur les motivations réelles du décideur afin de garantir leur pertinence et leur acceptabilité12.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Objectifs du dirigeant, niveau de maturité digitale perçu, volonté de changement2. |
| **Réponses typiques** | "Je veux passer moins de temps au bureau le week-end"24, "Je souhaite doubler mon chiffre d'affaires"6, "Je veux moderniser mes outils". |
| **Relance unique** | *"Si vous deviez identifier le plus grand obstacle qui vous empêche d'atteindre cet objectif aujourd'hui, quel serait-il ?"* [source 1] |
| **Boutons conseillés** | [Gagner du temps & de la sérénité]24 ; [Développer mon chiffre d'affaires]6 ; [Structurer mon équipe]25 |
| **Champ structuré YAML** | audit.goals.owner_ambition |
| **Impact livrable** | Définition du ton de la restitution du rapport et priorisation des recommandations selon l'impact personnel estimé pour le dirigeant. |

### **Étape 6 : operations_week**

* **Formulation d'Omar** : *"Si nous regardons votre dernière semaine de travail : quelle est la tâche, en dehors de votre cœur de métier, qui vous a pris le plus de temps ou qui a généré le plus de fatigue ? Le genre d'activité administrative ou d'organisation dont vous aimeriez vous libérer définitivement."*
  [source 12, 25]
* **Justification méthodologique** : Identification et quantification des inefficacités opérationnelles majeures (Lean Waste) pour cibler les automatisations à fort ROI12.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Tâches chronophages répétitives, intensité de la charge mentale, estimation du temps perdu12. |
| **Réponses typiques** | "Je passe mes soirées à rédiger des devis"33, "La gestion des plannings de mes serveurs m'épuise"25, "Je passe trop de temps à relancer les factures impayées"26. |
| **Relance unique** | *"Combien d'heures par semaine estimez-vous perdre sur cette tâche administrative ?"* [source 12] |
| **Boutons conseillés** | [La paperasse / Facturation]26 ; [La planification d'équipe]25 ; [Le suivi des clients & e-mails]6 |
| **Champ structuré YAML** | audit.operations.time_sinks |
| **Impact livrable** | Alimentation de l'indice de friction opérationnelle et définition de la mission de l'agent IA proposé12. |

### **Étape 7 : marketing_sales**

* **Formulation d'Omar** : *"Une fois qu'un prospect s'intéresse à vos services, sous quel délai et sous quel format lui transmettez-vous généralement votre proposition commerciale ou votre devis ?"*
* **Justification méthodologique** : Diagnostic de l'efficacité de l'entonnoir de vente et repérage des goulots d'étranglement de réactivité commerciale37.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Délai de traitement des demandes entrantes, format d'émission, taux de relance des devis en attente26. |
| **Réponses typiques** | "J'envoie un PDF par e-mail sous 3 jours", "Je fais mes devis sur place sur un carnet", "J'utilise un logiciel métier"26. |
| **Relance unique** | *"Relancez-vous systématiquement vos prospects s'ils ne répondent pas à vos devis sous une semaine ?"* [source 26, 38] |
| **Boutons conseillés** | [Envoi immédiat automatisé]38 ; [Envoi sous quelques jours] ; [Pas de relance systématique] |
| **Champ structuré YAML** | audit.sales.conversion_flow |
| **Impact livrable** | Section "Diagnostic Commercial" du rapport final et proposition d'automations de relance client. |

### **Étape 8 : admin_finance_purchasing**

* **Formulation d'Omar** : *"Comment gérez-vous le suivi de vos factures et les relances pour retards de paiement ? Utilisez-vous un outil dédié ou est-ce principalement géré de manière manuelle avec l'aide de votre comptable ?"*
  [source 1, 2]
* **Justification méthodologique** : Évaluation du degré de dématérialisation comptable et de la sensibilité aux retards de trésorerie25.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Outils de facturation, niveau de préparation à la facture électronique1, gestion des factures fournisseurs28. |
| **Réponses typiques** | "J'utilise un fichier Excel", "Mon expert-comptable gère tout", "J'ai un logiciel comme Tiime ou Obat"2. |
| **Relance unique** | *"Êtes-vous informé de l'obligation légale d'adopter un logiciel de facturation électronique d'ici septembre 2027 ?"* [source 1] |
| **Boutons conseillés** | [Logiciel de facturation conforme]1 ; [Fichiers Excel / Word]2 ; [Gestion manuelle / Papier] |
| **Champ structuré YAML** | audit.finance.invoicing_compliance |
| **Impact livrable** | Diagnostic réglementaire d'adéquation fiscale et d'opportunité d'automatisation des relances de paiement26. |

### **Étape 9 : hr_team_organization**

* **Formulation d'Omar** : *"Si vous travaillez avec des collaborateurs ou des sous-traitants, comment s'organise la planification de leurs tâches quotidiennes et la transmission des consignes de travail ?"*
  [source 25]
* **Justification méthodologique** : Évaluation de l'autonomie des collaborateurs et de l'adéquation des outils de planification interne25.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Taille de l'équipe, outils de planification (Skello, Combo, WhatsApp, Excel)25, formalisation des consignes. |
| **Réponses typiques** | "Je leur envoie des SMS", "On utilise un planning papier dans l'atelier", "On gère avec un logiciel de planning"25. |
| **Relance unique** | *"Rencontrez-vous régulièrement des erreurs de planning ou des oublis de consignes ?"* [source 24, 25] |
| **Boutons conseillés** | [Planning papier / WhatsApp]25 ; [Logiciel de planning d'équipe]25 ; [Dirigeant solo (Pas d'équipe)]15 |
| **Champ structuré YAML** | audit.hr.organization_tools |
| **Impact livrable** | Section "Organisation d'équipe" du rapport final. Recommandation d'interconnexion ou d'outils de planification spécialisés25. |

### **Étape 10 : digital_tools_data**

* **Formulation d'Omar** : *"Où conservez-vous la liste de vos contacts clients et l'historique de vos échanges avec eux ? Est-ce centralisé dans un outil ou dispersé entre vos e-mails, votre téléphone et vos carnets ?"*
  [source 2, 39]
* **Justification méthodologique** : Analyse de la maturité et de la centralisation des données de l'entreprise, prérequis indispensable pour l'intégration d'un agent IA performant2.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Base de données clients, niveau de centralisation, présence de ressaisies manuelles d'un outil à un autre2. |
| **Réponses typiques** | "Tout est dans mon téléphone", "On a un CRM", "J'ai un carnet et des fiches clients papier", "Plusieurs fichiers Excel"2. |
| **Relance unique** | *"Devez-vous souvent recopier manuellement des informations d'un outil à un autre au cours de la journée ?"* [source 2] |
| **Boutons conseillés** | [Centralisé dans un CRM]40 ; [Dispersé (E-mails / Excel)]2 ; [Papier uniquement] |
| **Champ structuré YAML** | audit.data.integration_level |
| **Impact livrable** | Diagnostic d'éligibilité technique à l'intégration d'un agent IA connecté et évaluation de l'indice de friction des données12. |

### **Étape 11 : risks_limits**

* **Formulation d'Omar** : *"Quelles sont les activités de votre entreprise sur lesquelles vous refusez catégoriquement de déléguer la prise de décision à un outil informatique, même s'il s'agit d'une assistance virtuelle ?"*
  [source 7, 18]
* **Justification méthodologique** : Identification des lignes rouges éthiques et stratégiques du dirigeant pour garantir la sécurité d'usage de l'automatisation7.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Lignes rouges d'automatisation, craintes éthiques, données hautement sensibles à exclure18. |
| **Réponses typiques** | "Je veux toujours valider le prix final des devis", "La relation humaine avec mes clients ne doit pas changer"24, "La validation comptable". |
| **Relance unique** | *"Une validation humaine systématique avant chaque envoi automatique de message ou de document vous rassurerait-elle ?"* [source 12, 18] |
| **Boutons conseillés** | [Validation humaine obligatoire]12 ; [Automatisation possible de bout en bout] ; [Refus de l'IA sur la relation client]24 |
| **Champ structuré YAML** | audit.governance.automation_redlines |
| **Impact livrable** | Inscription des règles de sécurité et des limites d'autonomie au sein du profil de l'agent IA généré (agent_profile). |

### **Étape 12 : diagnosis**

* **Formulation d'Omar** : *"D'après nos échanges, je commence à avoir une vision très claire de votre organisation. Si vous m'y autorisez, je vais structurer vos forces, vos axes d'amélioration, ainsi que les opportunités prioritaires de gain de temps sous forme d'une synthèse."*
  [source 10, 12]
* **Justification méthodologique** : Transition vers la phase de restitution, structuration sémantique du diagnostic (SWOT, friction, cyber)16.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Validation globale des données collectées par l'utilisateur. |
| **Réponses typiques** | "D'accord, montrez-moi ça", "Je veux corriger un point d'abord", "Allez-y". |
| **Relance unique** | *"Souhaitez-vous préciser ou modifier une information sur votre organisation avant que je ne génère l'analyse ?"* |
| **Boutons conseillés** | [Générer le diagnostic] ; [Modifier une déclaration d'audit] |
| **Champ structuré YAML** | audit.diagnosis.trigger_generation |
| **Impact livrable** | Déclenchement des appels d'API pour la génération du rapport final et calcul des indices de maturité. |

### **Étape 13 : recommendations**

* **Formulation d'Omar** : *"Voici les trois actions clés que j'ai identifiées pour simplifier votre quotidien. Laquelle de ces solutions vous semble la plus urgente et la plus pertinente à mettre en place dans votre entreprise ?"*
  [source 10, 12]
* **Justification méthodologique** : Co-conception de la feuille de route d'action pour s'assurer que le devis final sera aligné sur les choix validés du client10.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Choix prioritaire du client, intérêt d'implémentation d'un agent IA d'accompagnement. |
| **Réponses typiques** | "L'automatisation des relances de devis m'intéresse"26, "Je préfère d'abord sécuriser mes sauvegardes"8, "Rien pour l'instant". |
| **Relance unique** | *"Nous pouvons avancer pas à pas en commençant par la solution la plus simple à mettre en œuvre."* [source 10] |
| **Boutons conseillés** | [Sélectionner la recommandation 1] ; [Sélectionner la recommandation 2] ; [Je souhaite réfléchir] |
| **Champ structuré YAML** | audit.recommendations.selected_priorities |
| **Impact livrable** | Détermination des modules technologiques actifs dans le livrable de devis et d'onboarding de l'agent. |

### **Étape 14 : validation**

* **Formulation d'Omar** : *"Nous avons terminé notre parcours de diagnostic. Votre rapport de synthèse complet et gratuit est maintenant disponible. Pour la suite, que préférez-vous ? Souhaitez-vous obtenir une estimation de devis pour les solutions choisies, ou préférez-vous en discuter de vive voix avec Alex ?"*
* **Justification méthodologique** : Phase finale de l'audit conversationnel. Orientation non intrusive vers les prochaines actions de transformation.

| Paramètre Métadonnées | Définition Spécifique |
| :---- | :---- |
| **Signaux attendus** | Choix de la suite du parcours par l'utilisateur, niveau de satisfaction globale16. |
| **Réponses typiques** | "Je veux voir le devis", "Je souhaite un rendez-vous avec Alex", "Je préfère lire le rapport d'abord". |
| **Relance unique** | *"Votre rapport reste accessible à tout moment. Quelle décision vous semble la plus confortable aujourd'hui ?"* |
| **Boutons conseillés** | [Consulter le devis justifié] ; [Prendre rendez-vous avec Alex] ; [Télécharger le rapport gratuit] |
| **Champ structuré YAML** | audit.validation.next_step_selection |
| **Impact livrable** | Finalisation de l'audit, persistance des données et redirection de l'utilisateur vers l'interface de livraison choisie. |

## **5\. Moteur de Branchement et Règles d'Adaptation Dynamique**

Pour éviter un parcours d'audit rigide et linéaire, le moteur de dialogue d'AppOmar doit évaluer de manière dynamique l'état des variables d'entrée et ajuster le flux de questions. Les règles d'adaptation comportementale sont définies ci-dessous :

### **Règle 1 : Branchement Solo contre Équipe**

* **Déclencheur** : Variable workforce_slice issue de l'API SIRENE3 ou déclaration de l'utilisateur à l'étape 4\.
* **Comportement** : Si l'effectif est égal à zéro (dirigeant solo)15 :
  * Désactiver l'étape 9 (hr_team_organization).
  * Réorienter l'exploration de la charge mentale opérationnelle (operations_week) vers l'isolement administratif, l'optimisation des temps de facturation personnels24 et la simplification de la relation client directe.
  * Si l'effectif est supérieur ou égal à un : activer systématiquement l'exploration des outils de planification d'équipe (type Skello ou Combo25) et de la politique de sécurité des accès collaborateurs8.

### **Règle 2 : Branchement B2B contre B2C Local**

* **Déclencheur** : Variable target_audience issue de l'étape 4\.
* **Comportement** :
  * Si le profil est identifié comme **B2C Local** (commerces de proximité, boulangeries, restaurants)6 :
    * Masquer les questions complexes sur la négociation des devis et les factures de situation de travaux26.
    * Activer un module d'analyse sémantique automatique des avis publics en ligne et d'évaluation de l'attractivité sur Google Maps1.
    * Orienter l'évaluation sur l'expérience d'encaissement physique6.
  * Si le profil est identifié comme **B2B Prestations** (professions libérales, avocats, cabinets conseils)7 :
    * Activer les questions relatives au cycle d'affaires (temps de rédaction des propositions, taux de conversion des propositions, processus de relance des impayés26).

### **Règle 3 : Branchement selon le Temps de Disponibilité Déclaré**

* **Déclencheur** : Variable time_allocated_minutes à l'étape 1 (pacte).
* **Comportement** :
  * Si l'utilisateur choisit l'option "Audit Rapide (10 min)" :
    * Le moteur conversationnel compresse le parcours en fusionnant les étapes d'exploration. Il conserve uniquement : pacte [formule/score à normaliser] identity_public_context [formule/score à normaliser] operations_week [formule/score à normaliser] digital_tools_data [formule/score à normaliser] diagnosis [formule/score à normaliser] validation.
    * Les étapes d'analyse sectorielle fine, d'acquisition marketing et de gestion RH sont désactivées4.

### **Règle 4 : Gestion des Données Sensibles et Refus de Recherche Publique**

* **Déclencheur** : Refus de consentement à l'étape 3 (public_sources_consent).
* **Comportement** :
  * Désactiver immédiatement toutes les requêtes d'arrière-plan vers les outils d'exploration de site web ou de réseaux sociaux1.
  * L'agent d'audit applique une règle de "souveraineté déclarative" absolue : toutes les données d'identité ou d'outils doivent être collectées par le dialogue uniquement, sans aucune tentative d'enrichissement externe14.
  * Insérer une mention spéciale dans le rapport final indiquant le caractère strictement confidentiel et autonome des données d'audit.

## **6\. Recherche Publique Consentie, Traitement des Erreurs et RGPD**

L'interconnexion d'AppOmar avec les bases de données publiques françaises et européennes doit respecter un cadre juridique strict afin de préserver la confiance et la conformité légale de la TPE14.

### **Architecture d'enrichissement et traitement des divergences**

L'application AppOmar exploite en premier lieu l'API Recherche d'Entreprises pour valider l'existence de l'établissement à partir de l'identité officielle Sirene3. Le traitement des erreurs d'identification s'effectue selon la logique suivante :

* **Anomalie d'homonymie ou d'adresses multiples** : Si la requête textuelle retourne plusieurs établissements, l'agent conversationnel ne doit pas faire de choix arbitraire. Il affiche une carte de sélection épurée contenant les adresses associées et invite le dirigeant à cliquer sur son établissement exact.
* **Statut de non-diffusibilité Sirene** : Dans le cas d'une entreprise individuelle ayant demandé son retrait de la diffusion publique Sirene3, l'API retourne un code spécifique ou une absence de données. L'agent d'audit bascule immédiatement sur un mode de saisie manuelle guidée sans générer de message d'erreur bloquant.
* **Erreur d'adresse ou code NAF obsolète** : Si le client signale que les données de l'API Sirene ne correspondent pas à sa réalité opérationnelle (déménagement récent, changement d'activité non enregistré), l'agent conversationnel valide immédiatement la correction du client, l'enregistre en base, et applique un tag de traçabilité "Déclaré Client" prévalant sur la donnée publique pour la suite de l'audit.

### **Cadre RGPD et protection des données personnelles**

Pour se conformer aux exigences de la CNIL en matière de réutilisation de données publiques à des fins de diagnostic d'entreprise et de prospection B2B, les règles suivantes sont appliquées14 :

* **Consentement granulaire par source (Consent Gates)** : L'étape 3 requiert un consentement distinct pour l'analyse des registres d'État3, du site internet et de la fiche Google Business Profile1. L'acceptation des CGU de l'application ne vaut pas consentement pour ces traitements spécifiques14.
* **Minimisation des données collectées** : L'outil d'exploration de site web d'AppOmar doit uniquement analyser la structure sémantique (détermination des mots-clés métiers, présence d'outils d'encaissement ou de formulaires)1. Il est formellement interdit de collecter ou de stocker des adresses e-mails personnelles de collaborateurs ou de clients présentes sur le site web audité.
* **Droit d'opposition immédiat** : Lors de la restitution du rapport d'audit, une commande simple permet à l'utilisateur de demander la suppression instantanée de toutes les données d'enrichissement public collectées au cours de la session14.

## **7\. Modèle de Scoring Simple et Explicable**

Afin d'offrir au dirigeant une vision transparente et incontestable de son organisation, AppOmar s'appuie sur des indices mathématiques simples, calculés à partir des signaux validés.

### **Formulation des indices d'évaluation**

#### **1\. Indice d'Hygiène Cyber ([formule/score à normaliser])**

L'évaluation s'appuie sur la conformité aux exigences prioritaires d'hygiène de l'ANSSI8 :
[formule/score à normaliser]

* [formule/score à normaliser] : Score de [formule/score à normaliser] si la règle de sauvegarde 3-2-1 est respectée (sauvegarde externalisée déconnectée)8, [formule/score à normaliser] si sauvegarde cloud simple sans test de restauration2, [formule/score à normaliser] en l'absence de sauvegarde fiable.
* [formule/score à normaliser] : Score de [formule/score à normaliser] si utilisation d'authentification double facteur (MFA) sur la messagerie et de mots de passe uniques gérés en coffre-fort6, [formule/score à normaliser] si authentification simple mais mots de passe robustes, [formule/score à normaliser] si partage de mots de passe faibles8.
* [formule/score à normaliser] : Score de [formule/score à normaliser] si application automatique des correctifs sur les systèmes critiques8, [formule/score à normaliser] si gestion manuelle irrégulière.
* [formule/score à normaliser] : Score de [formule/score à normaliser] si sensibilisation ou formation active des collaborateurs aux risques de phishing8, [formule/score à normaliser] sinon.

#### **2\. Indice de Friction Opérationnelle ([formule/score à normaliser])**

Cet indice évalue la perte d'efficience liée aux tâches administratives répétitives :
[formule/score à normaliser]

* [formule/score à normaliser] : Nombre d'heures estimées consacrées à la tâche administrative répétitive [formule/score à normaliser] par semaine12.
* [formule/score à normaliser] : Coefficient de ressaisie manuelle de données associé à la tâche (de [formule/score à normaliser] pour aucune recopie à [formule/score à normaliser] pour des saisies multiples dans différents outils non interconnectés)2.
* [formule/score à normaliser] : Poids d'irritation émotionnelle ou de fatigue subjective déclaré par le dirigeant (échelle de [formule/score à normaliser] pour supportable à [formule/score à normaliser] pour insupportable)12.

#### **3\. Indice de Maturité Numérique et d'Adoption IA ([formule/score à normaliser])**

Inspiré de l'évaluation de maturité de l'OCDE18 :
[formule/score à normaliser]

* [formule/score à normaliser] : Niveau d'utilisation d'outils cloud et d'API intégrés au quotidien (de [formule/score à normaliser] pour aucun outil à [formule/score à normaliser] pour un écosystème SaaS interconnecté)27.
* [formule/score à normaliser] : Disponibilité de données métiers structurées (fichiers clients, historiques de facturation qualifiés)2.
* [formule/score à normaliser] : Appétence ou usage courant d'outils d'IA générative généralistes au sein de l'équipe1.
* [formule/score à normaliser] : Existence de règles ou politiques d'utilisation sécurisée des outils technologiques18.

### **Explicabilité et limites d'interprétation**

Chaque score calculé par l'IA d'AppOmar est présenté au dirigeant selon une grille d'explicabilité stricte :

[Indice d'Hygiène Cybersécurité : 45/100 (Maturité Intermédiaire)]
- Pourquoi ce score ? Ce résultat s'explique principalement par l'absence d'une copie de sauvegarde déconnectée physiquement (règle ANSSI 3-2-1), malgré la présence d'un antivirus actif et d'une double authentification sur votre boîte mail principale.
- Limite de l'analyse : Le diagnostic ne peut pas vérifier si vos sauvegardes cloud actuelles sont effectivement chiffrées et protégées contre les ransomwares.
- Comment progresser ? Vous pouvez améliorer immédiatement votre score de 20 points en mettant en place un disque de sauvegarde physique de vos fichiers clés, débranché de votre réseau chaque soir.

## **8\. Modèle de Rapport Final de Restitution**

Le rapport final de restitution d'AppOmar doit être structuré pour délivrer une valeur opérationnelle immédiate, en évitant les longs textes théoriques au profit d'analyses factuelles et exploitables.

### **Modèle de structure du rapport de restitution**

# RAPPORT DE DIAGNOSTIC BUSINESS & TECH — [Nom de l'Entreprise]
Date de génération : [Date] | Réf. Audit : [ID unique]
Auditeur virtuel : Omar pour AppOmar

## 1\. Résumé exécutif
[Synthèse narrative en 5 phrases présentant l'état de santé de la structure, sa maturité globale et le potentiel de gain de temps hebdomadaire estimé.]

## 2\. Déclarations du client (D)
- Principaux irritants identifiés : [Verbatim sur la tâche la plus lourde]
- Temps hebdomadaire perdu estimé : [Heures consacrées à l'administratif]
- Équipe et organisation : [Taille déclarée, processus de transmission des plannings]
- Lignes rouges de l'entrepreneur : [Processus exclus de l'automatisation]

## 3\. Sources vérifiées (V)
- Raison sociale et Siren : [Données issues de l'API SIRENE]
- Code d'activité NAF : [Code officiel de l'établissement]
- Présence web : [Statut du site internet, validation de la sécurité SSL]
- Fiche locale : [Nombre d'avis clients, note moyenne, taux de réponse]

## 4\. Hypothèses d'Omar (H)
- Gain d'efficacité financière : [Estimation de réduction du délai de paiement des factures]
- Alignement réglementaire : [Niveau d'effort requis pour la facturation électronique 2027]
- Risque d'interruption cyber : [Impact financier estimé en cas d'attaque par déni de service] [source 39]

## 5\. Diagnostic business
[Analyse narrative de la chaîne de création de valeur, des forces d'acquisition et des faiblesses d'entonnoir de vente.]

## 6\. Diagnostic tech/data
[Analyse des ruptures de flux logicielles, du niveau de centralisation des contacts et d'intégration des applications].

## 7\. Analyse SWOT
| Forces (S) | Faiblesses (W) |
| :--- | :--- |
| [Atouts internes identifiés] | [Ruptures de flux, dépendances humaines] |
| \*\*Opportunités (O)\*\* | \*\*Menaces (T)\*\* |
| [Automatisations IA à fort ROI] | [Obligations non respectées, risques cyber] [source 1, 8] |

## 8\. Risques et lignes rouges
[Définition des processus de l'entreprise qu'il est formellement recommandé de conserver sous contrôle humain exclusif pour préserver la confiance réglementaire ou la qualité de service].

## 9\. Matrice d'automatisation (Impact/Effort/Risque)
| Opportunité | Processus | Impact | Effort | Risque | Score Priorité |
| :--- | :--- | :---: | :---: | :---: | :---: |
| Opt_01 | [Nom de l'automatisation] | Fort | Faible | Négligeable | 9,5 / 10 |
| Opt_02 | [Nom de l'automatisation] | Moyen | Moyen | Faible | 6,8 / 10 |

## 10\. Quick wins (7 jours)
[Plan de 3 actions correctives immédiates, sans coût logiciel, pour améliorer la sécurité ou l'efficacité de la TPE].

## 11\. Plan d'action (30 jours)
[Recommandations d'interconnexion ou de déploiement d'outils d'automatisation prioritaires co-validés par le dirigeant].

## 12\. Recommandations OA (Omar & Alex)
[Présentation détaillée des solutions d'accompagnement proposées par AppOmar pour soutenir la feuille de route.]

## 13\. Limites d'automatisation
[Section rappelant les barrières de sécurité et les garde-fous de l'agent IA.]

## 14\. Prompts et procédures utiles
[Fourniture de 3 invites de commandes ou procédures pas-à-pas directement utilisables par le dirigeant sur des outils d'IA gratuits].

## 15\. Données d'onboarding agent
[Données de profilage structurées prêtes à être injectées pour la configuration de l'agent IA autonome.]

## 16\. Structure de devis justifié
[Présentation transparente de l'estimation budgétaire associée aux recommandations d'accompagnement AppOmar.]

## 17\. Prochaines décisions
[Options d'étapes suivantes proposées de manière non intrusive au dirigeant pour poursuivre sa démarche.]

### **Directives d'écriture et de mise en forme**

Le rapport doit impérativement utiliser des verbes d'action et éliminer tout terme anxiogène. En cas de faiblesse sur la cybersécurité, au lieu de formuler : *"Votre système informatique est vulnérable aux piratages"*46, préférer : *"La mise en place d'une sauvegarde externalisée déconnectée permettra de garantir la continuité de votre activité en cas d'incident sous 4 heures"*8.

## **9\. Modèle d'Onboarding de l'Agent IA (agent_profile)**

Afin de transformer instantanément l'audit conversationnel en une solution opérationnelle, AppOmar génère une fiche de configuration structurée (agent_profile) définissant l'identité, les compétences et les barrières de l'agent virtuel destiné à l'entreprise.

YAML
agent_profile:
  meta:
    agent_id: "oa.agent.btp_assistant_01"
    creation_date: "2026-07-08"
    status: "draft_pending_human_validation"

  identity:
    role: "Assistant de Coordination et Gestion Commerciale BTP"
    tone_profile: "Professionnel, calme, méthodique, extrêmement attentif aux terminologies du bâtiment"
    communication_channel: "E-mail professionnel (Gmail)"
    language_register: "Vouvoiement systématique des clients et sous-traitants"

  mission:
    core_objective: "Prendre en charge l'extraction des devis reçus des fournisseurs par e-mail, la pré-saisie des situations de travaux et la relance commerciale des propositions en attente" [source 26, 29]
    success_criteria:
      - "Réduction du délai d'envoi des factures d'acompte à moins de 24 heures après validation de chantier" [source 33, 38]
      - "Centralisation de 100 % des contacts clients de l'année dans Obat" [source 29]

  boundaries:
    authorized_actions:
      - "Analyser les e-mails de demande de devis entrants et rédiger des brouillons de propositions basées sur la grille tarifaire de l'entreprise"
      - "Extraire les mentions d'articles des factures fournisseurs par OCR" [source 29]
    prohibited_actions:
      - "Envoyer de manière autonome un e-mail ou une proposition commerciale à un client externe"
      - "Modifier directement les données d'assurance décennale ou d'immatriculation légale" [source 29, 33]
    human_in_the_loop_gates:
      - "Toute proposition de relance ou de devis rédigée par l'agent doit être explicitement validée par le dirigeant avant envoi" [source 12, 18]

  integrations:
    allowed_connectors:
      - "recherche-entreprises.api.gouv.fr" [source 3]
      - "obat_api_v1" [source 29]
    data_access_level: "Lecture-écriture restreinte sur le répertoire client et les brouillons de devis"
    forbidden_data_stores:
      - "Comptes d'administration système" [source 8]
      - "Données bancaires directes"

## **10\. Modèle de Devis Justifié et Pédagogique**

Pour éviter d'apparaître comme un outil commercial agressif, le devis proposé par AppOmar doit découler de manière transparente des recommandations d'amélioration validées par l'utilisateur au cours du diagnostic. Chaque option budgétaire s'accompagne de sa justification factuelle et de ses prérequis techniques11.
Le tableau ci-dessous présente la structure d'un devis d'accompagnement modulaire :

| Référence Catalogue | Recommandation Source | Verbatim / Preuve Client | Bénéfice Opérationnel Attendu | Prérequis Techniques | Limites d'Usage | Indice de Confiance | Statut Optionnel | Horizon de Déploiement | Tarif Estimé |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **OA-INTEG-01** | Automatisation du suivi des devis et relances38. | *"Je passe mes soirées à rédiger des devis et je n'ai pas le temps de les relancer."* [source 12, 33] | Libération de 4 heures administratives par semaine. Amélioration de 15 % du taux de conversion commerciale37. | Abonnement actif à un logiciel de facturation BTP agréé (ex: Obat)29. | L'agent ne négocie pas les rabais de prix de manière autonome. | [formule/score à normaliser] | Optionnel | Immédiat (Plan 7 jours)20 | [formule/score à normaliser] (Configuration unique) |
| **OA-CYBER-03** | Sécurisation et automatisation de la règle de sauvegarde 3-2-18. | *"Je n'ai pas de système de sauvegarde fiable et mes fichiers clients sont dispersés."* [source 2, 39] | Garantie de résilience totale des données d'activité en cas d'attaque par ransomware sous 4 heures8. | Configuration d'un compte cloud sécurisé et déploiement d'un disque de stockage physique6. | Nécessite la déconnexion manuelle quotidienne du support de sauvegarde physique8. | [formule/score à normaliser] | Hautement recommandé | Immédiat (Plan 7 jours)8 | [formule/score à normaliser] (Mise en service) |
| **OA-AGENT-05** | Configuration de l'agent IA de pré-rédaction des courriels. | *"Je perds trop de temps à répondre aux demandes d'information basiques par e-mail."* [source 12, 25] | Réduction de 60 % du temps consacré à la gestion de la boîte mail de contact. | Messagerie professionnelle compatible IMAP/SMTP ou API Google Workspace. | Validation humaine obligatoire de chaque brouillon rédigé avant envoi12. | [formule/score à normaliser] | Optionnel | Différé (Plan 30 jours)10 | [formule/score à normaliser] (Entraînement et déploiement) |

## **11\. Spécification YAML Enrichie**

Le code suivant représente la structure enrichie de l'arbre d'audit de l'application AppOmar (src/audit_tree.business_tech.v2.yaml), conçue pour intégrer de manière dynamique les contrôles de consentement, les branchements adaptatifs et la traçabilité des sources de données.

YAML
audit_tree:
  meta:
    schema_version: "oa.audit-tree/1"
    release_date: "2026-07-08"
    author: "AppOmar Core Team"

  acts:
    - id: "rencontre"
      validation_mode: "act_validation"
      steps:
        - id: "pacte"
          type: "conversational_gate"
          rules:
            open_question_ratio: 0.70
            max_follow_up_attempts: 1
          inputs:
            user_consent:
              type: "boolean"
              required: true
            time_allocated_minutes:
              type: "integer"
              allowed_values: [10, 20, 30]
          ui_controls:
            buttons:
              - label: "Démarrer l'audit complet (20 min)"
                value: 20
              - label: "Faire le parcours rapide (10 min)"
                value: 10

        - id: "identity_public_context"
          type: "api_integration_gate"
          endpoint: "https://recherche-entreprises.api.gouv.fr"
          require_consent: true
          consent_scope: "sirene_database_lookup"
          inputs:
            siren_or_name:
              type: "string"
              required: true
            city:
              type: "string"
              required: false
          validations:
            - field: "siren"
              regex: "^\\\\d{9}$"
          outputs:
            structured_data:
              siren: "siren"
              company_name: "nom_raison_sociale"
              code_naf: "activite_principale"
              workforce_slice: "tranche_effectif"
            ui_card: "company_validation_card"

        - id: "public_sources_consent"
          type: "consent_gate"
          inputs:
            consent_sirene:
              type: "boolean"
              required: true
            consent_website:
              type: "boolean"
              required: true
            consent_google_maps:
              type: "boolean"
              required: true

    - id: "plongee"
      validation_mode: "act_validation"
      steps:
        - id: "operations_week"
          type: "conversational_exploration"
          inputs:
            chronophagous_tasks_description:
              type: "text"
              required: true
            emotional_load_level:
              type: "integer"
              allowed_values: [1, 2, 3]
          branch_rules:
            - condition: "workforce_slice \== '0'"
              target_step: "admin_finance_purchasing"
            - condition: "workforce_slice \!= '0'"
              target_step: "hr_team_organization"

        - id: "hr_team_organization"
          type: "conversational_exploration"
          inputs:
            planning_tool:
              type: "string"
              allowed_values: ["paper", "excel", "specialized_software", "none"]
            consign_transmission_method:
              type: "string"
              allowed_values: ["oral", "messenger", "written_procedure"]

        - id: "admin_finance_purchasing"
          type: "conversational_exploration"
          inputs:
            invoicing_tool_type:
              type: "string"
              allowed_values: ["compliant_software", "word_excel", "paper"]
            electronic_invoicing_awareness:
              type: "boolean"
              required: true

        - id: "cyber_backup"
          type: "cyber_security_baseline"
          inputs:
            backup_strategy:
              type: "string"
              allowed_values: ["none", "cloud_auto", "manual_external", "unknown"]
            mfa_enabled:
              type: "boolean"
              required: true
          scoring_impact:
            cyber_score:
              formula: "backup_strategy \== 'cloud_auto' ? 4 : (backup_strategy \== 'manual_external' ? 2 : 0)"

    - id: "livraison"
      validation_mode: "client_signoff"
      steps:
        - id: "diagnosis_generation"
          type: "ai_synthesis"
          engine: "alex-diagnosis-engine"
          inputs_map:
            - "operations_week.chronophagous_tasks_description"
            - "cyber_backup.backup_strategy"
          outputs:
            report_payload: "outputs.report"
            onboarding_payload: "outputs.onboarding"
            devis_payload: "outputs.devis"

## **12\. Répertoire des Ressources et Liens Officiels**

Afin de garantir la mise à jour réglementaire et technique d'AppOmar, le système s'appuie sur les portails institutionnels suivants :

* **France Num** : Le portail gouvernemental pour l'accompagnement à la transformation numérique des TPE et PME françaises. [https://www.francenum.gouv.fr](https://www.francenum.gouv.fr)1.
* **Annuaire des Entreprises / API Recherche d'Entreprises** : Le moteur officiel de l'État pour rechercher et valider l'identité légale d'un établissement. [https://annuaire-entreprises.data.gouv.fr](https://annuaire-entreprises.data.gouv.fr)3.
* **ANSSI (Agence Nationale de la Sécurité des Systèmes d'Information)** : Recommandations de sécurité, guides d'hygiène et formations d'auto-évaluation. [https://cyber.gouv.fr](https://cyber.gouv.fr)8.
* **Cybermalveillance.gouv.fr** : Plateforme d'assistance aux victimes de malveillance informatique et d'évaluation de la maturité cyber. [https://www.cybermalveillance.gouv.fr](https://www.cybermalveillance.gouv.fr)39.
* **CNIL (Commission Nationale de l'Informatique et des Libertés)** : Directives sur la réutilisation des données personnelles et les règles de prospection commerciale. [https://www.cnil.fr](https://www.cnil.fr)13.
* **Bpifrance Diagnostics** : Accompagnement, subventions d'État et programmes d'évaluation de la maturité Data/IA. [https://diag.bpifrance.fr](https://diag.bpifrance.fr)10.

## **13\. Recommandations Concrètes de Modification de l'Arbre YAML Actuel**

La comparaison entre l'arbre de référence initial (src/audit_tree.business_tech.v1.yaml) et les meilleures pratiques identifiées par l'analyse comparative met en évidence plusieurs axes d'amélioration opérationnels à intégrer lors du merge :

### **Écarts identifiés et corrections à apporter**

1. **Intégration du module de consentement RGPD (public_sources_consent)** : L'arbre de référence de Fable prévoit une étape de consentement, mais celle-ci doit être structurée sous forme de commutateurs indépendants (Sirene3, site internet1, Google Profile4) à l'étape 3 plutôt qu'une acceptation globale, afin d'assurer la conformité CNIL14.
2. **Ajout d'une évaluation cyber pragmatique** : Remplacer les questions générales sur la sécurité informatique par le module cyber_backup centré sur les trois exigences de base de l'ANSSI (application de la sauvegarde 3-2-1, activation de l'authentification multi-facteurs, usage d'un coffre-fort de mots de passe)8.
3. **Mise en place de la traçabilité des données d'audit (D/V/H/F)** : Modifier le schéma oa.audit-tree/1 pour imposer que chaque champ d'information extrait lors des actes 1 et 2 porte une étiquette de traçabilité claire, interdisant le recours à des transcriptions brutes sans distinction d'origine.
4. **Génération automatisée des livrables de sortie** : L'acte de livraison final ne doit plus être une simple validation textuelle, mais doit déclencher de manière asynchrone la création de trois objets distincts en base : le rapport structuré conforme au modèle de restitution, le profil d'onboarding de l'agent IA (agent_profile) et la proposition commerciale modulaire sous forme de devis d'accompagnement.
5. **Prise en compte des risques opérationnels liés aux agents IA** : Inscrire au sein de la section de gouvernance de l'audit un garde-fou technique interdisant l'automatisation complète de processus sensibles sans passerelle de validation humaine systématique (human_in_the_loop)12.

#### **Sources des citations**

1. Baromètre France Num 2025 : le numérique et l'intelligence artificielle dans les TPE et PME - francenum.gouv.fr, [https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-le](https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-le)
2. Baromètre France Num 2025 : résultats de l'enquête qualitative - francenum.gouv.fr, [https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-resultats](https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-resultats)
3. API Recherche d'Entreprises | data.gouv.fr, [https://www.data.gouv.fr/dataservices/api-recherche-dentreprises](https://www.data.gouv.fr/dataservices/api-recherche-dentreprises)
4. Mon Diag'Num – Diagnostic de maturité numérique 100 % financé | CCI Paris Ile-de-France, [https://www.entreprises.cci-paris-idf.fr/offres/mon-diagnostic-de-maturite-numerique](https://www.entreprises.cci-paris-idf.fr/offres/mon-diagnostic-de-maturite-numerique)
5. Transformation numérique des TPE/PME : les enseignements du baromètre 2025 de France Num | economie.gouv.fr, [https://www.economie.gouv.fr/actualites/transformation-numerique-des-tpepme-les-enseignements-du-barometre-2025-de-france-num](https://www.economie.gouv.fr/actualites/transformation-numerique-des-tpepme-les-enseignements-du-barometre-2025-de-france-num)
6. Baromètre France Num 2025 : le numérique et l'IA dans les TPE et PME de l'hébergement-restauration - francenum.gouv.fr, [https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-le-0](https://www.francenum.gouv.fr/guides-et-conseils/strategie-numerique/comprendre-le-numerique/barometre-france-num-2025-le-0)
7. OECD: AI Adoption by Small and Medium-Sized Enterprises - Libertify.com, [https://www.libertify.com/interactive-library/oecd-ai-adoption-smes/](https://www.libertify.com/interactive-library/oecd-ai-adoption-smes/)
8. LA CYBERSÉCURITÉ POUR LES TPE/PME EN 13 QUESTIONS - ANSSI, [https://messervices.cyber.gouv.fr/documents-guides/20241212_np_anssi_guide_tpe-pme_v2.pdf](https://messervices.cyber.gouv.fr/documents-guides/20241212_np_anssi_guide_tpe-pme_v2.pdf)
9. Cyber Départ | ANSSI - Campus Région du numérique, [https://campusnumerique.auvergnerhonealpes.fr/dispositifs/diag-cyber-depart-anssi/](https://campusnumerique.auvergnerhonealpes.fr/dispositifs/diag-cyber-depart-anssi/)
10. Diagnostic IA Bpifrance : comment en bénéficier en 2026 - Bloom, [https://www.bloom-ai.fr/blog/diagnostic-ia-bpifrance](https://www.bloom-ai.fr/blog/diagnostic-ia-bpifrance)
11. Diag Data IA - Bpifrance, [https://www.bpifrance.fr/catalogue-offres/diag-data-ia](https://www.bpifrance.fr/catalogue-offres/diag-data-ia)
12. Diag Data IA Bpifrance : une méthodologie d'audit orientée impact - Galadrim, [https://galadrim.fr/blog/diag-data-ia-bpifrance-une-methodologie-daudit-orientee-impact/](https://galadrim.fr/blog/diag-data-ia-bpifrance-une-methodologie-daudit-orientee-impact/)
13. La prospection vers les particuliers (B to C) : quelles règles pour transmettre des données à des partenaires ? | CNIL, [https://www.cnil.fr/fr/la-prospection-b-to-c-quelles-regles-pour-transmettre-des-donnees-des-partenaires](https://www.cnil.fr/fr/la-prospection-b-to-c-quelles-regles-pour-transmettre-des-donnees-des-partenaires)
14. Réutilisation de vos données publiées sur Internet à des fins commerciales : quels sont vos droits ? | CNIL, [https://www.cnil.fr/fr/reutilisation-de-vos-donnees-publiees-sur-internet-des-fins-commerciales-quels-sont-vos-droits](https://www.cnil.fr/fr/reutilisation-de-vos-donnees-publiees-sur-internet-des-fins-commerciales-quels-sont-vos-droits)
15. Baromètre France Num — Ministère de l'Économie, des Finances et de la Souveraineté industrielle, énergétique et numérique - Data Economie, [https://data.economie.gouv.fr/pages/barometre-france-num/](https://data.economie.gouv.fr/pages/barometre-france-num/)
16. Cahier des Charges Diagnostic Data - Intelligence artificielle - Diag'Inno Bpifrance, [https://diaginno.bpifrance.fr/storage/sites/2/2023/02/DIAG-DATA-IA-Cahier-des-Charges_VF.pdf](https://diaginno.bpifrance.fr/storage/sites/2/2023/02/DIAG-DATA-IA-Cahier-des-Charges_VF.pdf)
17. Diag Data IA - Diagnostic Accompagnement - Bpifrance, [https://diag.bpifrance.fr/diag-data-ia](https://diag.bpifrance.fr/diag-data-ia)
18. SME AI Readiness Tool – OECD, [https://sme.oecd.ai/](https://sme.oecd.ai/)
19. G7 Industry, Digital and Technology Ministerial Statement on the SME AI Adoption Blueprint, [https://www.g7.utoronto.ca/ict/2025-sme-ai-adoption-blueprint.html](https://www.g7.utoronto.ca/ict/2025-sme-ai-adoption-blueprint.html)
20. Découvrez MesServicesCyber : le catalogue des solutions cyber gratuites pour les TPE PME - francenum.gouv.fr, [https://www.francenum.gouv.fr/decouvrez-messervicescyber-le-catalogue-des-solutions-cyber-gratuites-pour-les-tpe-pme](https://www.francenum.gouv.fr/decouvrez-messervicescyber-le-catalogue-des-solutions-cyber-gratuites-pour-les-tpe-pme)
21. Mon Aide Cyber : le CIG vous accompagne - CIG Grande Couronne, [https://www.cigversailles.fr/actualites/mon-aide-cyber-le-cig-vous-accompagne](https://www.cigversailles.fr/actualites/mon-aide-cyber-le-cig-vous-accompagne)
22. Le diagnostic cyber gratuit - MesServicesCyber, [https://messervices.cyber.gouv.fr/services/mon-aide-cyber.html](https://messervices.cyber.gouv.fr/services/mon-aide-cyber.html)
23. Sirene, le répertoire gratuit des entreprises | economie.gouv.fr, [https://www.economie.gouv.fr/entreprises/gerer-son-entreprise-au-quotidien/gerer-sa-comptabilite-et-ses-demarches/sirene-le](https://www.economie.gouv.fr/entreprises/gerer-son-entreprise-au-quotidien/gerer-sa-comptabilite-et-ses-demarches/sirene-le)
24. Boulangerie : Boostez vos ventes grâce à la digitalisation - FIDUCIAL, [https://www.fiducial.fr/Pointex-logiciel-caisse/Blog-pour-les-professionnels-de-la-restauration/Boostez-les-ventes-de-votre-boulangerie-grace-a-la-digitalisation](https://www.fiducial.fr/Pointex-logiciel-caisse/Blog-pour-les-professionnels-de-la-restauration/Boostez-les-ventes-de-votre-boulangerie-grace-a-la-digitalisation)
25. Quels sont les meilleurs logiciels pour votre boulangerie ? - Combo, [https://combohr.com/fr/blog/logiciel-boulangerie](https://combohr.com/fr/blog/logiciel-boulangerie)
26. Top 10 des meilleurs logiciels de devis et facturation pour les artisans - Blog Tiime, [https://blog.tiime.fr/top-10-meilleurs-logiciels-de-devis-et-facturation-artisans](https://blog.tiime.fr/top-10-meilleurs-logiciels-de-devis-et-facturation-artisans)
27. Les meilleurs logiciels de facturation pour avocat 2026 - Indy, [https://www.indy.fr/guide/facturation/logiciel/avocat/](https://www.indy.fr/guide/facturation/logiciel/avocat/)
28. Les 7 meilleurs logiciels pour votre boulangerie en 2026 - Skello, [https://www.skello.io/blog/meilleurs-logiciels-boulangerie](https://www.skello.io/blog/meilleurs-logiciels-boulangerie)
29. Comparatif logiciels artisan BTP 2026 : Obat, Tolteck, Axonaut vs ArtisanSmart, [https://artisansmart.fr/blog/comparatif-logiciel-artisan-2026/](https://artisansmart.fr/blog/comparatif-logiciel-artisan-2026/)
30. Logiciel de gestion de temps - Avocat - Tempolia, [https://www.tempolia.fr/gestion-de-temps-avocats.htm](https://www.tempolia.fr/gestion-de-temps-avocats.htm)
31. La prospection commerciale | CNIL, [https://www.cnil.fr/fr/la-prospection-commerciale](https://www.cnil.fr/fr/la-prospection-commerciale)
32. La prospection commerciale par courrier électronique, SMS-MMS et automate d'appel, [https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel](https://www.cnil.fr/fr/la-prospection-commerciale-par-courrier-electronique-sms-mms-et-automate-dappel)
33. Mediabat - Logiciel devis facture batiment pour les artisans du BTP, [https://www.mediabat.com/](https://www.mediabat.com/)
34. Logiciel de facturation pour avocat : obligations et comparatif 2026 - Qonto, [https://qonto.com/fr/blog/gestion-entreprise/facturation/logiciel-facturation-avocat](https://qonto.com/fr/blog/gestion-entreprise/facturation/logiciel-facturation-avocat)
35. Diagnostic digital : sécurisez votre projet numérique - CCI Alsace Eurométropole, [https://www.alsace-eurometropole.cci.fr/produit/diagnostic-digital-securisez-votre-projet-numerique](https://www.alsace-eurometropole.cci.fr/produit/diagnostic-digital-securisez-votre-projet-numerique)
36. ProGBat : Logiciel BTP tout-en-un | Gérez vos chantiers efficacement, [https://www.progbat.com/](https://www.progbat.com/)
37. Logiciel artisan bâtiment : comparatif 2026 des meilleures solutions pour pros du BTP, [https://www.go-kelvin.com/ressources/logiciel-artisan-batiment-comparatif-2026-des-meilleures-solutions-pour-pros-du-btp](https://www.go-kelvin.com/ressources/logiciel-artisan-batiment-comparatif-2026-des-meilleures-solutions-pour-pros-du-btp)
38. Top 7 des logiciels de devis et factures pour le bâtiment en 2026 - Qonto, [https://qonto.com/fr/blog/gestion-entreprise/btp-construction/logiciel-devis-facture-batiment](https://qonto.com/fr/blog/gestion-entreprise/btp-construction/logiciel-devis-facture-batiment)
39. GUIDE CYBERSÉCURITÉ - Cybermalveillance.gouv, [https://www.cybermalveillance.gouv.fr/medias/2021/05/Guide-de-cybersecurite-a-destination-des-dirigeants-de-TPE-PME-et-ETI.pdf](https://www.cybermalveillance.gouv.fr/medias/2021/05/Guide-de-cybersecurite-a-destination-des-dirigeants-de-TPE-PME-et-ETI.pdf)
40. Le top 10 des logiciels indispensables aux avocats - N2F, [https://www.n2f.com/blog/top-10-des-logiciels-indispensables-aux-avocats/](https://www.n2f.com/blog/top-10-des-logiciels-indispensables-aux-avocats/)
41. Top 7 logiciels CGP 2026 : comparatif (prix \+ avis) - Support Majors, [https://support.majors.finance/ressources/top-7-logiciels-CGP-2026.html](https://support.majors.finance/ressources/top-7-logiciels-CGP-2026.html)
42. Quel logiciel de caisse choisir pour sa boulangerie - MAPA Assurances, [https://www.mapa-assurances.fr/boulangerie/logiciel-caisse-boulangerie](https://www.mapa-assurances.fr/boulangerie/logiciel-caisse-boulangerie)
43. Logiciel de caisse pour boulangerie : les fonctionnalités incontournables à connaître, [https://retail-shops.orisha.com/blog/metier/boulangers/logiciel-caisse-boulangerie-fonctionnalites/](https://retail-shops.orisha.com/blog/metier/boulangers/logiciel-caisse-boulangerie-fonctionnalites/)
44. 2ème édition du baromètre national de la maturité cyber des TPE-PME, [https://www.cybermalveillance.gouv.fr/tous-nos-contenus/actualites/etude-maturite-cyber-tpe-pme-2025](https://www.cybermalveillance.gouv.fr/tous-nos-contenus/actualites/etude-maturite-cyber-tpe-pme-2025)
45. Cybersécurité : des dispositifs publics gratuits pour vous accompagner | economie.gouv.fr, [https://www.economie.gouv.fr/entreprises/gerer-son-entreprise-au-quotidien/assurer-sa-cybersecurite-et-la-protection-de-ses-1](https://www.economie.gouv.fr/entreprises/gerer-son-entreprise-au-quotidien/assurer-sa-cybersecurite-et-la-protection-de-ses-1)
46. La cybersécurité pour les TPE/PME en 13 questions | Direction générale des Entreprises, [https://www.entreprises.gouv.fr/la-dge/actualites/la-cybersecurite-pour-les-tpepme-en-13-questions](https://www.entreprises.gouv.fr/la-dge/actualites/la-cybersecurite-pour-les-tpepme-en-13-questions)

