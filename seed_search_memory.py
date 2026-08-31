# ORYN - Preenche a memória de pesquisa com buscas em lote (gerador automático).
# Uso: python seed_search_memory.py [inicio] [quantidade]
#      Ex.: python seed_search_memory.py 0 700   (busca do índice 0 ao 699)
import sys
import sqlite3
import time

sys.stdout.reconfigure(encoding="utf-8")

import app

TOPICS = [
    # Tecnologia
    "inteligência artificial", "aprendizado de máquina", "chatgpt", "programação", "python",
    "javascript", "java", "c++", "linux", "windows", "bash", "docker", "kubernetes",
    "git", "github", "banco de dados", "sql", "nuvem", "computador", "celular",
    "smartphone", "notebook", "roteador", "wifi", "impressora", "teclado mecânico",
    "monitor", "processador", "placa de vídeo", "memória ram", "ssd", "fonte de alimentação",
    "gabinete", "headset", "webcam", "microfone", "câmera digital", "drone", "robô",
    "impressora 3d", "blockchain", "bitcoin", "criptomoeda", "nft", "metaverso",
    "realidade virtual", "realidade aumentada", "computação quântica", "5g", "bluetooth",
    "usb", "cabo de rede", "sensor", "circuito eletrônico", "arduino", "raspberry pi",
    "aplicativo", "site", "servidor", "domínio", "email", "redes sociais",
    # Ciência
    "física", "química", "biologia", "matemática", "astronomia", "geologia", "biologia marinha",
    "genética", "evolução", "dna", "célula", "vírus", "bactéria", "buraco negro",
    "planeta", "estrela", "galáxia", "lua", "sol", "cometa", "meteoro",
    "fotossíntese", "ecossistema", "biodiversidade", "aquecimento global", "energia solar",
    "energia eólica", "energia nuclear", "reciclagem", "efeito estufa", "camada de ozônio",
    "terremoto", "vulcão", "tsunami", "furacão", "clima", "previsão do tempo",
    # Saúde
    "sono", "ansiedade", "depressão", "estresse", "alimentação saudável", "dieta", "jejum",
    "vitamina", "mineral", "cálcio", "ferro", "proteína", "carboidrato", "gordura",
    "pressão alta", "diabetes", "colesterol", "obesidade", "coração", "cérebro", "músculo",
    "ossos", "articulação", "pele", "cabelo", "visão", "audição", "dor de cabeça",
    "gripe", "resfriado", "febre", "insônia", "alongamento", "exercício físico",
    "corrida", "caminhada", "musculação", "ioga", "pilates", "natação", "bicicleta",
    # Comida
    "arroz", "feijão", "carne", "frango", "peixe", "ovo", "leite", "queijo", "iogurte",
    "café", "chá", "suco", "cerveja", "vinho", "chocolate", "bolo", "pão", "massa",
    "pizza", "hambúrguer", "sushi", "feijoada", "moqueca", "churrasco", "açaí", "fruta",
    "banana", "maçã", "manga", "abacaxi", "melancia", "morango", "uva", "laranja",
    # Esportes
    "futebol", "futsal", "basquete", "vôlei", "handebol", "tênis", "golfe", "xadrez",
    "e-sports", "atletismo", "maratona", "ciclismo", "boxe", "jiu-jitsu", "judô", "capoeira",
    "natação olímpica", "skate", "surfe", "escalada", "copa do mundo", "copa américa",
    "olimpíadas", "fórmula 1", "futebol americano", "beisebol", "críquete", "rugby",
    # História e geografia
    "segunda guerra mundial", "primeira guerra mundial", "guerra fria", "império romano",
    "egito antigo", "grécia antiga", "idade média", "renascimento", "revolução industrial",
    "descobrimento do brasil", "independência do brasil", "escravidão", "zumbi dos palmares",
    "bandeirantes", "ciclode da borracha", "ciclode do ouro", "café no brasil",
    "estados do brasil", "cidades do brasil", "rio amazonas", "amazonas", "pantanal",
    "serra gaúcha", "chapada", "litoral do brasil", "praia", "montanha", "deserto",
    "vulcão ativo", "maior país do mundo", "menor país do mundo", "capital do brasil",
    "cidades do mundo", "oceano", "mars", "marte", "lua azul",
    # Cultura e entretenimento
    "música", "samba", "pagode", "funk", "sertanejo", "forró", "axé", "rock", "pop",
    "mpb", "jazz", "blues", "clássico", "eletrônica", "guitarra", "violão", "piano",
    "bateria", "cinema", "filme", "série", "novela", "anime", "desenho", "mangá",
    "quadrinhos", "livros", "poesia", "arte", "pintura", "fotografia", "teatro", "dança",
    "balé", "moda", "estilo", "tatuagem", "piercing", "cabelo", "barba",
    # Economia e finanças
    "poupança", "renda fixa", "renda variável", "ações", "fii", "tesouro direto", "cdb",
    "lci", "tesouro selic", "bolsa de valores", "imposto de renda", "inss", "pix",
    "investimento", "reserva de emergência", "juros compostos", "inflação", "selic",
    "dólar", "euro", "criptomoeda", "ouro", "imóvel", "aluguel", "financiamento",
    # Trabalho e educação
    "currículo", "entrevista de emprego", "freelance", "home office", "empreendedorismo",
    "startup", "pequena empresa", "marketing digital", "publicidade", "vendas",
    "atendimento ao cliente", "sebrae", "mei", "clt", "pj", "direitos trabalhistas",
    "faculdade", "curso técnico", "enem", "vestibular", "bolsa de estudos", "ead",
    # Diversos
    "cuidados com pet", "gato", "cachorro", "papagaio", "coelho", "aquário", "peixes ornamentais",
    "jardinagem", "plantas", "vasos", "horta", "pragas", "diy", "artesanato", "costura",
    "culinária", "limpeza", "organização", "mudança de casa", "decoração", "iluminação",
    "climatização", "eletrodoméstico", "máquina de lavar", "geladeira", "fogão", "forno",
    "viagem", "hotel", "turismo", "passaporte", "visto", "cruzeiro", "acampamento",
    # Ferramentas do dia a dia 2026
    "node.js", "react", "typescript", "flutter", "android studio", "excel", "power bi",
    "google sheets", "automação de tarefas", "cli", "powershell", "segurança de senhas",
    "antivírus", "vpn", "backup na nuvem", "google drive", "onedrive", "chatbot",
    "api", "web scraping", "inteligência artificial generativa", "stable diffusion",
    "comfyui", "texto para voz", "transcrição de áudio", "editor de vídeo", "canva",
    "photoshop", "gimp", "figma", "marcas", "aquecimento de hidrogênio",
    # Games e entretenimento
    "minecraft", "roblox", "fortnite", "free fire", "league of legends", "valorant",
    "counter strike", "zelda", "god of war", "gta", "nintendo switch", "playstation 5",
    "xbox", "pc gamer", "netflix", "youtube", "twitch", "prime video", "disney plus",
    "animes populares", "mangás populares",
    # Finanças do cotidiano (BR)
    "cartão de crédito", "score de crédito", "serasa", "débito automático",
    "open finance", "cashback", "cartão de débito", "cheque especial",
    "consórcio", "seguro de vida", "condomínio", "iptu", "ipva", "cnh", "seguro do carro",
    # Tecnologia nova
    "celular dobrável", "carro elétrico", "carregador rápido", "moto 5g", "smartwatch",
    "realidade mista", "casa inteligente", "assistente de voz", "carro autônomo",
    "inteligência artificial em medicina", "computador de bolso",
    # Manutenção e segurança
    "limpar pc", "organizar fotos", "recuperar arquivo deletado", "formatar computador",
    "upgrade de hardware", "overclock", "segurança wifi", "phishing", "golpe online",
    "golpe do pix", "senha forte", "autenticação em duas etapas", "conta bancária brasileira",
]

# ---- Expansão massiva (quase "Wikipedia") ----
# Países e capitais (gerados programaticamente)
COUNTRIES_CAPITALS = [
    ("Brasil", "Brasília"), ("Estados Unidos", "Washington"), ("Canadá", "Ottawa"),
    ("México", "Cidade do México"), ("Argentina", "Buenos Aires"), ("Chile", "Santiago"),
    ("Peru", "Lima"), ("Colômbia", "Bogotá"), ("Venezuela", "Caracas"), ("Equador", "Quito"),
    ("Bolívia", "La Paz"), ("Paraguai", "Assunção"), ("Uruguai", "Montevidéu"),
    ("Guiana", "Georgetown"), ("Suriname", "Paramaribo"), ("Guiana Francesa", "Caiena"),
    ("Belize", "Belmopã"), ("Guatemala", "Guatemala"), ("Honduras", "Tegucigalpa"),
    ("El Salvador", "San Salvador"), ("Nicarágua", "Manágua"), ("Costa Rica", "San José"),
    ("Panamá", "Cidade do Panamá"), ("Cuba", "Havana"), ("Jamaica", "Kingston"),
    ("Haiti", "Porto Príncipe"), ("República Dominicana", "Santo Domingo"),
    ("Bahamas", "Nassau"), ("Trinidad e Tobago", "Porto da Espanha"), ("Puerto Rico", "San Juan"),
    (# Europa
    "Portugal", "Lisboa"), ("Espanha", "Madri"), ("França", "Paris"), ("Reino Unido", "Londres"),
    ("Alemanha", "Berlim"), ("Itália", "Roma"), ("Holanda", "Amsterdã"), ("Bélgica", "Bruxelas"),
    ("Suíça", "Berna"), ("Áustria", "Viena"), ("Irlanda", "Dublin"), ("Escócia", "Edimburgo"),
    ("País de Gales", "Cardiff"), ("Dinamarca", "Copenhague"), ("Noruega", "Oslo"),
    ("Suécia", "Estocolmo"), ("Finlândia", "Helsinque"), ("Islândia", "Reykjavík"),
    ("Polônia", "Varsóvia"), ("República Tcheca", "Praga"), ("Eslováquia", "Bratislava"),
    ("Hungria", "Budapeste"), ("Romênia", "Bucareste"), ("Bulgária", "Sófia"),
    ("Grécia", "Atenas"), ("Croácia", "Zagreb"), ("Sérvia", "Belgrado"), ("Bósnia", "Sarajevo"),
    ("Albânia", "Tirana"), ("Ucrânia", "Kiev"), ("Bielorrússia", "Minsk"),
    ("Rússia", "Moscou"), ("Estônia", "Tallinn"), ("Letônia", "Riga"), ("Lituânia", "Vilna"),
    (# Ásia
    "China", "Pequim"), ("Japão", "Tóquio"), ("Coreia do Sul", "Seul"),
    ("Coreia do Norte", "Pyongyang"), ("Índia", "Nova Délhi"), ("Paquistão", "Islamabade"),
    ("Bangladesh", "Daca"), ("Sri Lanka", "Colombo"), ("Nepal", "Catmandu"),
    ("Butão", "Timphu"), ("Afeganistão", "Cabul"), ("Irã", "Teerã"), ("Iraque", "Bagdá"),
    ("Síria", "Damasco"), ("Líbano", "Beirute"), ("Israel", "Jerusalém"), ("Jordânia", "Amã"),
    ("Arábia Saudita", "Riad"), ("Emirados Árabes", "Dubai"), ("Catar", "Doha"),
    ("Kuwait", "Kuwait"), ("Omã", "Mascate"), ("Iêmen", "Sana"), ("Turquia", "Istambul"),
    ("Cazaquistão", "Astana"), ("Uzbequistão", "Tashkent"), ("Mongólia", "Ulan Bator"),
    ("Indonésia", "Jacarta"), ("Malásia", "Kuala Lumpur"), ("Singapura", "Singapura"),
    ("Tailândia", "Bangkok"), ("Vietnã", "Hanói"), ("Filipinas", "Manila"),
    ("Mianmar", "Nepiedó"), ("Camboja", "Phnom Penh"), ("Laos", "Vientiane"),
    (# África
    "Egito", "Cairo"), ("Nigéria", "Abuja"), ("África do Sul", "Pretória"),
    ("Quênia", "Nairóbi"), ("Etiópia", "Adis Abeba"), ("Tanzânia", "Dar es Salaam"),
    ("Uganda", "Kampala"), ("Gana", "Acra"), ("Camarões", "Iaundê"), ("Costa do Marfim", "Iamussucro"),
    ("Senegal", "Dacar"), ("Marrocos", "Rabat"), ("Argélia", "Argel"), ("Tunísia", "Túnis"),
    ("Líbia", "Trípoli"), ("Sudão", "Cartum"), ("Angola", "Luanda"), ("Moçambique", "Maputo"),
    ("Zâmbia", "Lusaca"), ("Zimbábue", "Harare"), ("Botsuana", "Gaborone"), ("Namíbia", "Vinduque"),
    (# Oceania
    "Austrália", "Camberra"), ("Nova Zelândia", "Wellington"), ("Fiji", "Suva"),
    ("Papua Nova Guiné", "Port Moresby"), ("Ilhas Salomão", "Honiara"),
    (# Américas
    "Guiana", "Georgetown"),
]

GEO_EXTRA = [
    "montanhas dos andes", "alpes", "himalaia", "monte everest", "deserto do saara",
    "deserto de atacama", "floresta amazônica", "mata atlântica", "cerrado", "caatinga",
    "pampa", "araucárias", "rio nilo", "rio mississipi", "rio danúbio", "rio ganges",
    "mar mediterrâneo", "mar caribenho", "mar morto", "mar vermelho", "oceano pacífico",
    "oceano atlântico", "oceano índico", "oceano ártico", "oceanos do mundo",
    "maior deserto do mundo", "cachoeira do iguaçu", "cataratas do niágara",
    "grand canyon", "aurora boreal", "tundra", "savana", "taiga", "pantanal mato-grossense",
    "ilha de férias", "arquipélago", "atol", "recife de coral", "grande barreira de corais",
    "cidade do vaticano", "venezuela capital", "brasília arquitetura",
]

# Comidas internacionais
FOOD_WORLD = [
    "tacos", "burrito", "guacamole", "fajitas", "poutine", "hot dog", "pretzel",
    "paella", "tapas", "gazpacho", "croissant", "baguete", "ratatouille", "quiche",
    "crème brûlée", "macaron", "crepe", "cassoulet", "boeuf bourguignon", "escargot",
    "fish and chips", "shepherd's pie", "bangers and mash", "yorkshire pudding",
    "scone", "trifle", "bratwurst", "schnitzel", "weisswurst", "spätzle", "strudel",
    "sauerbraten", "pierogi", "goulash", "wiener schnitzel", "polenta", "risco al lima",
    "pizza napolitana", "lasanha", "ravióli", "gnocchi", "fettuccine", "carbonara",
    "penne", "risoto", "ossobuco", "panna cotta", "tiramisu", "gelato",
    "sashimi", "tempura", "okonomiyaki", "takoyaki", "ramen", "udon", "soba",
    "gyoza", "onigiri", "mochi", "matcha", "dango", "tonkatsu", "yakitori",
    "kimchi", "bibimbap", "bulgogi", "galbi", "tteokbokki", "pho", "bánh mì",
    "pad thai", "tom yum", "som tam", "satay", "nasi goreng", "rendang",
    "gado-gado", "curry", "tikka masala", "biriyani", "naan", "samosa",
    "masala dosa", "butter chicken", "kebab", "shawarma", "falafel", "hummus",
    "tabule", "pita", "baklava", "dolma", "kabsa", "tagine", "couscous",
    "mechoui", "injera", "jollof rice", "fufu", "suya", "chakalaka",
    "empanada", "arepa", "arepa rellena", "ceviche", "lomo saltado", "pisco sour",
    "causa", "papa a la huancaína", "feijão tropeiro", "pão de queijo", "brigadeiro",
    "coxinha", "pastel", "acarajé", "vatapá", "caruru", "baião de dois", "tacacá",
    "tapioca", "beijinho", "curau", "pamonha", "canjica", "pudim", "quindim",
    "mousse de maracujá", "farofa", "vinagrete", "molho de pimenta", "porco a portuguesa",
    "bacalhau", "pastel de nata", "francesinha", "cozido à portuguesa", "caldo verde",
    "piri-piri", "medalhão de filé", "picanha", "costela", "fraldinha", "dobradinha",
    "jabá", "carne seca", "rabada", "linguiça", "salsicha", "pernil", "lombo",
    "cupim", "fralda", "alcatra", "maminha", "ponta de peito",
]

# Personalidades
PERSONALITIES = [
    "albert einstein", "isaac newton", "nikola tesla", "thomas edison",
    "stephen hawking", "marie curie", "charles darwin", "galileu", "leonardo da vinci",
    "michelangelo", "platão", "sócrates", "aristóteles", "nietzsche", "marx",
    "freud", "jung", "einstein", "newton", "niels bohr", "max planck",
    "richard feynman", "alan turing", "grace hopper", "ada lovelace",
    "bill gates", "elon musk", "steve jobs", "jeff bezos", "mark zuckerberg",
    "larry page", "sergey brin", "tim berners-lee", "linus torvalds", "linus pauling",
    "johannes gutenberg", "walt disney", "pablo picasso", "van gogh", "monet",
    "da vinci", "machado de assis", "dom pedro segundo", "getúlio vargas",
    "jair bolsonaro", "lula", "nelson mandela", "martin luther king", "hill da gandhi",
    "napoleão", "julio cesar", "alexandre o grande", "cleópatra", "moisés",
    "jesus cristo", "maomé", "buda", "confúcio", "santo agostinho",
    "madre teresa", "frida kahlo", "coco chanel", "audrey hepburn", "meryl streep",
    "morgan freeman", "will smith", "robert de niro", "al pacino", "tom hanks",
    "leonardo dicaprio", "brad pitt", "angelina jolie", "nicole kidman", "julia roberts",
    "eiza gonzález", "penélope cruz", "javier bardem", "antonio banderas",
    "pele", "maradona", "cristiano ronaldo", "messi", "neymar", "ronaldinho",
    "rivaldo", "kaká", "roberto carlos", "arnold schwarzenegger", "robin williams",
    "bruce lee", "jackie chan", "silvester stallone", "dwayne johnson",
    "oprah winfrey", "michelle obama", "barack obama", "donald trump", "biden",
]

# Filmes e séries
MOVIES_SERIES = [
    "titanic", "avatar", "interestelar", "inception", "matrix", "senhor dos anéis",
    "harry potter", "star wars", "vingadores", "homem de ferro", "batman", "superman",
    "homem-aranha", "wolverine", "x-men", "guardiões da galáxia", "pantera negra",
    "jurassic park", "de volta para o futuro", "et", "o poderoso chefão", "pulp fiction",
    "clube da luta", "cidade de deus", "central do brasil", "auto da compadecida",
    "tropa de elite", "kung fu panda", "shrek", "frozen", "rei leão", "alien",
    "predador", "terminator", "brilho eterno", "memento", "seven", "silêncio dos inocentes",
    "gladiador", "braveheart", "prenda de um filme", "forrest gump", "green mile",
    "coco", "divertidamente", "moana", "encanto", "encanto colombia",
    "game of thrones", "breaking bad", "the walking dead", "stranger things",
    "the office", "friends", "how i met your mother", "the big bang theory",
    "the crown", "dark", "la casa de papel", "elite", "squid game", "vikingos",
    "peaky blinders", "the mandalorian", "wide western", "the witcher", "lupin",
    "berlim", "sem limites", "supernatural", "lost", "prison break", "succession",
    "the last of us", "money heist", "house of cards", "downton abbey",
    "marco polo", "o mundo de wolf", "better call saul", "ozark", "mindhunter",
]

# Músicos e artistas
MUSICIANS = [
    "the beatles", "queen", "rolling stones", "led zeppelin", "pink floyd",
    "nirvana", "metallica", "iron maiden", "acdc", "guns n' roses", "bon jovi",
    "u2", "coldplay", "linkin park", "red hot chili peppers", "imagine dragons",
    "maroon 5", "one direction", "backstreet boys", "nsync", "spice girls",
    "michael jackson", "elvis presley", "madonna", "britney spears", "beyoncé",
    "rihanna", "lady gaga", "adele", "taylor swift", "billie eilish", "ariana grande",
    "selena gomez", "justin bieber", "ed sheeran", "bruno mars", "katy perry",
    "shakira", "enrique iglesias", "ricky martin", "lady gaga",
    "roberto carlos", "caetano veloso", "gilberto gil", "gal costa", "maria bethânia",
    "chico buarque", "tom jobim", "vinícius de moraes", "elis regina", "tim maia",
    "djavan", "jorge ben jor", "seu jorge", "milton nascimento", "ivete sangalo",
    "claudia leitte", "anitta", "ludmilla", "ivy", "mc rabelo", "mari fernandez",
    "gustavo lima", "jorge e mateus", "marília mendonça", "ze neto e cristiano",
    "henrique e juliano", "bruno e marrone", "daniel e samuel", "chitãozinho e xororó",
    "zeca pagodinho", "martinho da vila", "beth carvalho", "josé augusto",
    "grupo revelação", "exaltasamba", "charlie brown jr", "apital", "skank",
    "titanic band", "legião urbana", "engenheiros do hawaii", "paralamas", "titas",
    "capital inicial", "cbjr", "osa vizinhos", "matanza", "angra", "sepultura",
]

# Memes e termos da internet
MEMES_INTERNET = [
    "meme", "viral", "trending", "modinha", "gif", "emoji", "meme do dia",
    "dogecoin", "meme de gato", "meme de cachorro", "shiba inu", "pfp", "avatar meme",
    "among us", "fnaf", "meme da risada", "rickroll", "ok boomer", "sus", "lol",
    "omg", "roflmao", "xprolado", "meme do negrito", "meme do vibe", "carinha desconfiada",
    "mãe diná", "mãe do tiktok", "tiktoker", "influencer", "youtuber", "streamer",
    "cringe", "stampede", "fyp", "hashtag", "viralização", "algorítmo do tiktok",
    "shorts", "reels", "story", "live", "instagram", "whatsapp", "telegram",
    "discord", "reddit", "tumblr", "pinterest", "snapchat", "beReal",
    "gamer", "viral do x", "meme do x", "internet quântica", "dark web",
    "deep web", "fake news", "desinformação", "plágio", "copyright", "memecoin",
]

# MAIS comida BR e mundo
FOOD_EXTRA = [
    "feijão", "carne de sol", "queijo coalho", "mel", "ovos de pascoa",
    "bolo de chocolate", "torta de limão", "cheesecake", "brownie", "cookies",
    "donut", "cupcake", "macaron", "churros", "algodão doce", "pirulito",
    "bala de goma", "jujuba", "chiclete", "kinder ovo", "nutella", "oreo",
    "snickers", "twix", "kitkat", "skittles", "gummy bear", "haribo",
    "pops", "sorvete de massa", "picolé", "milkshake", "açaí na tigela",
    "fondue", "raclete", "vários tipos de vinho", "vinho tinto", "vinho branco",
    "espumante", "prosecco", "champagne", "whisky", "tequila", "vodka", "rum",
    "gin", "licor", "caipirinha", "mojito", "piña colada", "margarita",
]

# Time de futebol
FOOTBALL_TEAMS = [
    "flamengo", "palmeiras", "corinthians", "são paulo", "santos", "grêmio",
    "internacional", "cruzeiro", "atlético mineiro", "fluminense", "botafogo",
    "vasco", "bahia", "vitória", "fortaleza", "ceará", "sport recife",
    "naútico", "goiás", "atlético goianiense", "coritiba", "athletico paranaense",
    "cuiabá", "juventude", "red bull bragantino", "américa mineiro", "criciúma",
    "chapecoense", "avaí", "figueirense", "csa", "bragantino", "seleção brasileira",
    "real madrid", "barcelona", "manchester united", "manchester city", "liverpool",
    "arsenal", "chelsea", "bayern de munique", "borussia dortmund", "juventus",
    "milão", "inter de milão", "paris saint-germain", "ajax", "porto", "benfica",
    "sporting", "boca juniors", "river plate", "nacional do uruguai", "peñarol",
    "barcelona de guayaquil", "flamengo 2019", "seleção brasileira 2002",
    "seleção brasileira 1970", "pelé santos", "maracanã", "copa libertadores",
]

# Estados e capitais do Brasil
BRAZIL_STATES = [
    "amazonas", "pará", "rondônia", "acre", "roraima", "tocantins", "amapá",
    "maranhão", "piauí", "ceará", "rio grande do norte", "paraíba", "pernambuco",
    "alagoas", "sergipe", "bahia", "minas gerais", "espírito santo", "rio de janeiro",
    "são paulo", "paraná", "santa catarina", "rio grande do sul", "mato grosso",
    "mato grosso do sul", "goiás", "distrito federal",
]
BRAZIL_CITIES = [
    "são paulo", "rio de janeiro", "salvador", "brasília", "fortaleza", "belo horizonte",
    "manaus", "curitiba", "recife", "porto alegre", "belém", "goiânia", "guarulhos",
    "campinas", "são luís", "maceió", "campo grande", "niterói", "joinville", "florianópolis",
    "santos", "ribeirão preto", "são josé dos campos", "uberlândia", "sorocaba",
    "londrina", "cuiabá", "joão pessoa", "natal", "teresina", "aracaju", "vitória",
    "macapá", "boa vista", "porto velho", "rio branco", "palmas", "campinas",
    "gramado", "blumenau", "paraty", "ouro preto", "ilhéus", "lençóis maranhenses",
    "bonito ms", "foz do iguaçu", "balneário camboriú", "campos do jordão",
]

# Universidades / instituições
UNIVERSITIES = [
    "usp", "unicamp", "unifesp", "unesp", "ufrj", "ufmg", "ufrgs", "unesp",
    "uff", "ufsc", "ufpr", "ufpe", "ufba", "ufpa", "ufc", "unb", "ufg",
    "ufes", "ufam", "ufmt", "uerj", "ita", "ime", "poli usp", "famerp",
    "enem", "fies", "prouni", "sisu", "puc", "mackenzie", "anhembi morumbi",
    "senai", "senac", "sebrae", "capes", "cnpq", "aiesp", "futura",
    "ifsp", "ufsm", "ufla", "ufv", "ufop", "ufscar", "unesp",
    "harvard", "oxford", "mit", "stanford", "cambridge", "yale", "princeton",
]

# Empresas e marcas do Brasil
COMPANIES = [
    "vale", "petrobras", "itau", "bradesco", "santander", "banco do brasil",
    "caixa economica", "nubank", "picpay", "inter", "c6 bank", "magazine luiza",
    "americanas", "casas bahia", "renner", "c&a", "zara", "havaianas",
    "natasha", "cacau show", "boticário", "o boticário", "embraer",
    "marcopolo", "ambev", "brahma", "skol", "antarctica", "italiano",
    "natura", "avon", "sadia", "perdigão", "seara", "jbs", "minerva",
    "walmart", "carrefour", "grupo pão de açúcar", "assai", "atacadão",
    "ifood", "rappi", "99", "uber no brasil", "gol", "latam", "azul",
    "tv globo", "globo", "sbt", "record", "band", "uol", "g1",
    "mcdonald's no brasil", "subway", "burger king", "habib's", "spoleto",
]

# Animais populares
ANIMALS = [
    "leão", "tigre", "onça", "leopardo", "guepardo", "elefante", "girafa",
    "rinoceronte", "hipopótamo", "zebra", "cavalo", "burro", "boi", "vaca",
    "ovelha", "cabra", "porco", "cabra", "galinha", "galo", "pato", "ganso",
    "peru", "avestruz", "pinguim", "coruja", "águia", "falcão", "gavião",
    "papagaio", "tucano", "beija-flor", "canário", "codorna", "pomba", "urubu",
    "cobra", "crocodilo", "jacaré", "lagarto", "iguana", "tartaruga", "jabuti",
    "sapo", "rã", "salamandra", "tubarão", "baleia", "golfinho", "orca",
    "peixe-beta", "tilápia", "salmão", "atum", "polvo", "lula", "caranguejo",
    "camarão", "lagosta", "cavalo-marinho", "estrela-do-mar", "cachorro",
    "gato", "coelho", "hamster", "furão", "rato", "camundongo", "esquilo",
    "macaco", "gorila", "chimpanzé", "orangotango", "panda", "urso pardo",
    "urso polar", "lobo", "raposa", "coiote", "hiena", "mangusto", "suricato",
    "canguru", "coala", "ornitorrinco", "tamanduá", "tatu", "capivara",
    "bicho-preguiça", "arara-azul", "mico-leão-dourado", "tucano-toco",
]

# Feriados, datas e história do Brasil
HOLIDAYS_DATE = [
    "dia das mães", "dia dos pais", "dia das crianças", "dia dos namorados",
    "dia do trabalho", "dia da independência", "dia de finados", "carnaval",
    "páscoa", "sexta-feira santa", "corpus christi", "dia da consciência negra",
    "reveillon", "ano novo", "festa junina", "são joão", "são pedro", "são marcos",
    "dia das bruxas", "halloween", "natal", "dia de são joão", "carnaval no brasil",
    "revolução de 1930", "proclamação da república", "revolução farroupilha",
    "guerra do paraguai", "inconfidência mineira", "revolta da vacina",
    "revolta da chibata", "canudos", "cangaço", "lampião", "bandeirantes",
    "capitania hereditária", "colonização do brasil", "era vargas", "ditadura militar",
    "abertura democrática", "diretas já", "plano real", "constituição de 1988",
    "redemocratização", "eleições diretas", "pré-sal", "guerra dos farrapos",
    "missões jesuíticas", "quilombos", "escravidão no brasil", "abolição da escravatura",
]

# Doenças e sintomas comuns
DISEASES = [
    "gripe", "resfriado", "covid", "dengue", "zika", "chikungunya", "febre amarela",
    "malária", "tuberculose", "pneumonia", "bronquite", "asma", "rinite", "sinusite",
    "amigdalite", "otite", "conjuntivite", "gastrite", "úlcera", "refluxo",
    "intoxicação alimentar", "diarréia", "constipação", "hérnia", "apendicite",
    "cálculo renal", "infecção urinária", "cistite", "hepatite", "cirrose", "gordura no fígado",
    "pancreatite", "diabetes tipo 1", "diabetes tipo 2", "hipertensão", "colesterol alto",
    "infarto", "avc", "arritmia", "insuficiência cardíaca", "aneurisma", "trombose",
    "anemia", "leucemia", "linfoma", "câncer de mama", "câncer de próstata",
    "câncer de pele", "câncer de pulmão", "câncer de colon", "tumor cerebral",
    "artrite", "artrose", "osteoporose", "gota", "fibromialgia", "lupus",
    "esclerose múltipla", "parkinson", "alzheimer", "epilepsia", "enxaqueca",
    "mal de parkinson", "depressão", "ansiedade", "burnout", "tdah", "autismo",
    "bipolaridade", "esquizofrenia", "insônia", "apneia do sono", "ronco",
    "vergonha", "fobia", "síndrome do pânico", "toca em conta", "dermatite",
    "psoríase", "acne", "eczema", "micose", "herpes", "sífilis", "gonorreia",
    "hiv", "aids", "verruga", "furúnculo", "unha encravada", "cárie", "gengivite",
]

# Religião e filosofia
RELIGION = [
    "cristianismo", "catolicismo", "protestantismo", "evangélico", "islamismo",
    "judaísmo", "budismo", "hinduísmo", "espiritismo", "umbanda", "candomblé",
    "xamanismo", "confucionismo", "taoismo", "sikhismo", "ateísmo", "agnosticismo",
    "bíblia", "alcorão", "torá", "vedas", "evangelho", "rezar", "oração",
    "igreja", "mesquita", "sinagoga", "templo", "padre", "pastor", "papa",
    "frei", "monges", "freiras", "batismo", "comunhão", "confissão", "missa",
    "filosofia", "estoicismo", "epicurismo", "existencialismo", "utilitarismo",
    "niilismo", "idealismo", "materialismo", "lógica", "ética", "moral",
    "cosmologia", "metafísica", "epistemologia", "hermenêutica", "socráticos",
]

# Esportes e atividades
SPORTS_EXTRA = [
    "basquete nba", "volei de praia", "futebol americano nfl", "hóquei no gelo",
    "beisebol mlb", "críquete", "rugby", "handebol", "waterpolo", "polo aquático",
    "ginástica artística", "ginástica rítmica", "halterofilismo", "levantamento de peso",
    "luta olímpica", "judô olímpico", "taekwondo", "karatê", "boxe olímpico",
    "esgrima", "tiro esportivo", "tiro com arco", "pentatlo", "triatlo",
    "canoagem", "remo", "vela", "surfe olímpico", "skate olímpico", "escalada esportiva",
    "badminton", "ping-pong", "tênis de mesa", "squash", "racquetball",
    "boliche", "bilhar", "sinuca", "dardos", "pesca esportiva", "caça",
    "paraglider", "paraquedismo", "bungee jump", "rafting", "canyoning",
    "esqui", "snowboard", "patinação no gelo", "patinação artística", "montanhismo",
    "trekking", "trilha", "acampamento", "paintball", "airsoft", "laser tag",
    "corrida de rua", "maratona", "meia maratona", "crossfit", "funcional",
    "hiit", "pilates", "zumba", "dança de salão", "forró", "samba de roda",
]

# Escrita, carreira e estudos
CAREER_WRITING = [
    "redação", "dissertação", "tese", "monografia", "artigo científico", "resenha",
    "resumo", "fichamento", "trabalho acadêmico", "normas abnt", "formatação abnt",
    "citações", "referências bibliográficas", "paráfrase", "coesão textual",
    "crase", "concordância", "regência", "pontuação", "vírgula", "acentuação",
    "novo acordo ortográfico", "português para concurso", "interpretação de texto",
    "comunicação", "oratória", "apresentação", "slide", "reunião", "networking",
    "entrevista", "teste psicológico", "dinâmica de grupo", "carreira", "promoção",
    "salário", "negociação salarial", "plano de carreira", "desenvolvimento pessoal",
    "produtividade", "gestão de tempo", "priorização", "sistema pomodoro",
    "mindset", "mentalidade", "hábitos", "metas", "planejamento", "organização",
    "curriculum vitae", "carta de apresentação", "portfólio", "linkedin",
    "perfil profissional", "marcapessoal", "autoconhecimento", "inteligência emocional",
]

# Tecnologia nova 2026
TECH_NEW_2026 = [
    "chatgpt 5", "grok", "gemini", "claude", "copilot", "meta ai", "deepseek",
    "llama", "mistral", "stable diffusion", "midjourney", "dall-e", "sora",
    "suno", "elevenlabs", "whisper", "transcrição automática", "tradução automática",
    "agente de ia", "ia agêntica", "multimodal", "ragged", "sql rag", "llm",
    "fine-tuning", "prompt engineering", "token", "alucinação", "contexto largo",
    "quantização", "inferência local", "ollama", "comfyui workflow", "flux",
    "wan", "img2vid", "texto para imagem", "texto para vídeo", "upscale",
    "restauração de imagem", "remoção de fundo", "geração de voz", "clonagem de voz",
    "robótica", "humanoide", "nebula bot", "automação residencial", "smart house",
    "ia de saúde", "ia na educação", "ia no direito", "ia no marketing",
    "cibersegurança de ia", "deepfake", "ai watermark", "regulação de ia",
    "ia ética", "privacidade de dados", "lgpd", "lgpd na prática",
]

# Mais destinos turísticos no mundo
TRAVEL_MORE = [
    "paris", "roma", "lisboa", "londres", "nova york", "dubai", "toquio",
    "barcelona", "madrid", "amsterdam", "praga", "veneza", "florença", "berlim",
    "viena", "budapeste", "estambul", "bangcoc", "singapura", "sydney", "melbourne",
    "toronto", "vancouver", "los angeles", "las vegas", "miami", "orlando",
    "cidade do mexico", "lima", "santiago", "buenos aires", "montevideu",
    "cartagena", "havana", "cancun", "punta cana", "praia do caribe",
    "ilha de páscoa", "machu picchu", "torre eiffel", "big ben", "coliseu",
    "estátua da liberdade", "cristo redentor", "muralha da china", "taj mahal",
    "coliseu de roma", "acrópole de atenas", "piramides de giza", "grand canyon",
    "campos de lavanda", "santorini", "costa amalfitana", "bali", "maldives",
    "bora bora", "tailandia", "dominicana", "porto de galinhas", "jericoacoara",
    "fernando de noronha", "chapada dos veadeiros", "bonito", "recife antigo",
    "olinda", "salvador pelourinho", "são miguel dos milagres", "canção do vale",
]

# Biografias brasileiras e figuras públicas
BRAZILIAN_PEOPLE = [
    "rodrigo faro", "ludovia", "whindersson nunes", "felipe neto", "casimiro",
    "jorge fernando", "márcia sensível", "tati quebra barraco", "mc pipokinha",
    "teto", "ana castela", "simone mendes", "maraisa", "maiara", "azevedo",
    "gusttavo lima", "leo santana", "claudia raia", "paola oliveira", "debora secco",
    "fernanda torres", "selton mello", "wagner moura", "lázaro ramos", "rodrigo santoro",
    "leandro hassum", "toni ramos", "bruna marquezine", "taís araújo", "lázaro",
    "sabrina sato", "maisa", "fernando e sorocaba", "marcos e belutti",
    "alok", "vintage culture", "zeca ribeiro", "romero brito", "creuza",
    "pelé biografia", "nascimento de pelé", "garrincha", "sócrates jogador",
    "rivellino", "zico", "falcao", "junior", "zagallo", "telê santana",
    "gabriel pensador", "marcelo d2", "mv bill", "sabotage", "racionais",
]

# Países adicionais (África, Ásia, ilhas e pequenas nações)
COUNTRIES_MORE = [
    "burundi", "chade", "comores", "congo", "república democrática do congo",
    "djibouti", "eritréia", "essuatíni", "gabão", "gâmbia", "guiné", "guiné-bissau",
    "guiné equatorial", "lesoto", "liberia", "madagascar", "malauí", "mali",
    "mauritânia", "maurício", "niger", "ruanda", "são tomé e príncipe",
    "seicheles", "serra leoa", "somália", "sudão do sul", "togo", "zimbábue",
    "brunei", "butão", "cambodja", "chipre", "filipinas", "geórgia", "ilhas marshall",
    "ilhas salomão", "jordânia", "kiribati", "laos", "maldivas", "micronésia",
    "mongólia", "nauru", "palau", "papua-nova-guiné", "samoa", "timor-leste",
    "tonga", "tuvalu", "vanuatu", "armênia", "azerbaijão", "cazaquistão",
    "quirguistão", "tadjiquistão", "turcomenistão", "bósnia e herzegovina",
    "macedônia", "montenegro", "eslovênia", "kosovo", "mônaco", "luxemburgo",
    "liechtenstein", "andorra", "são marino", "malta", "cyprus norte",
    "guernsey", "jersey", "ilha de man", "groelândia", "fernando de noronha",
    "trindade e martim vaz", "ilha de santa helena", "foz do iguaçu",
]

# Ciência avançada e natureza
SCIENCE_NATURE = [
    "física quântica", "mecânica quântica", "relatividade", "teoria das cordas",
    "partícula elementar", "bóson de higgs", "matéria escura", "energia escura",
    "big bang", "multiverso", "buracos de minhoca", "espaço-tempo", "singularidade",
    "supernova", "estrela de nêutrons", "pulsar", "quasar", "nebulosa", "constelação",
    "via láctea", "sistema solar", "planetas anões", "plutão", "cometa", "asteroide",
    "cinturão de asteroides", "meteoro", "meteorito", "eclipse", "eclipse solar",
    "eclipse lunar", "marte colonização", "lua fase", "fases da lua", "marés",
    "planeta terra", "atmosfera", "camadas da terra", "tectônica de placas",
    "deriva continental", "pangeia", "erosão", "sedimentação", "rochas", "minerais",
    "pedras preciosas", "diamante", "esmeralda", "rubi", "safira", "cristal",
    "fósseis", "dinossauros", "tiranossauro", "triceratops", "velociraptor",
    "pterodáctilo", "mastodonte", "mamute", "eras geológicas", "cambriano",
    "jurássico", "cretáceo", "pré-história", "evolução humana", "hominídeos",
    "neandertal", "primeiros humanos", "homo sapiens", "bípedes",
    "célula eucariota", "célula procariota", "mitocôndria", "núcleo celular",
    "cloroplasto", "atp", "proteínas", "enzimas", "hormônios", "hormônios do crescimento",
    "sistema nervoso", "neurônios", "sinapse", "cérebro humano", "hemisfério cerebral",
    "sistema circulatório", "coração humano", "artérias", "veias", "sangue",
    "glóbulos vermelhos", "glóbulos brancos", "plaquetas", "sistema imunológico",
    "anticorpos", "vacinas", "sistema digestivo", "estômago", "intestino",
    "fígado", "rins", "sistema respiratório", "pulmões", "sistema muscular",
    "sistema esquelético", "pele humana", "olho humano", "visão humana",
    "reprodução humana", "gravidez", "nascimento", "envelhecimento",
]

# Termos médicos e exames
MEDICAL_TERMS = [
    "exame de sangue", "hemograma", "glicemia", "hemoglobina", "colesterol",
    "triglicerídeos", "exame de urina", "exame de fezes", "ultrassom", "raio-x",
    "tomografia", "ressonância magnética", "eletrocardiograma", "ecocardiograma",
    "endoscopia", "colonoscopia", "biópsia", "papanicolau", "mamografia",
    "psa", "teste de gravidez", "teste de covid", "teste rápido", "vacinação",
    "cartão de vacina", "calendário de vacinas", "vacina da gripe", "vacina do covid",
    "antitérmico", "analgésico", "anti-inflamatório", "antibiótico", "antialérgico",
    "antidepressivo", "ansiolítico", "vitamina d", "suplemento", "probiótico",
    "prebiótico", "calmante", "reposição hormonal", "pressão arterial",
    "batimento cardíaco", "saturação", "oxigênio no sangue", "imc", "índice de massa corporal",
    "peso ideal",     "calorias", "gasto calórico", "metabolismo", "metabolismo basal", "fadiga",
    "tontura", "enjoo", "náusea", "vômito", "cólica", "dor de estômago",
    "dor nas costas", "dor no joelho", "dor de coluna", "dor muscular",
    "dor de garganta", "tosse", "espirro", "congestão nasal", "falta de ar",
    "palpitação", "suor noturno", "perda de apetite", "ganho de peso",
    "perda de peso", "cansaço", "sonolência", "clareza de pele", "pele ressecada",
    "queda de cabelo", "caspa", "unhas fracas", "olheiras", "espinhas",
]

# Cultura pop asiática (K-drama, anime, j-drama)
ASIA_POP = [
    "k-drama", "dorama", "k-pop", "bts", "blackpink", "twice", "exo", "super junior",
    "girls' generation", "nct", "stray kids", "ateez", "itzy", "aespa", "newjeans",
    "seventeen", "enhypen", "txt", "rnb coreano", "boa", "hwang in-yeop",
    "squid game detalhes", "parasita filme", "ilha da alegria", "o jogo da morte",
    "dark k-drama", "romance k-drama", "crime k-drama", "terror k-drama",
    "anime", "mangá", "one piece", "naruto", "dragon ball", "attack on titan",
    "demon slayer", "jujutsu kaisen", "my hero academia", "fullmetal alchemist",
    "death note", "cowboy bebop", "evangelion", "jogo dos anéis", "solo leveling",
    "chainsaw man", "kaiju nº 8", "spy x family", "frieren", "violet evergarden",
    "your name", "perfeito azul", "oulast do mundo", "made in abyss",
    "castle in the sky", "spirited away", "howl's moving castle", "totoro",
    "studio ghibli", "hayao miyazaki", "silent voice", "weathering with you",
    "suzume", "look back", "kaiju nº 8", "freiren", "jujutsu infinito",
    "japão cultura", "coreia cultura", "china cultura", "viska", "hanbok",
    "kimono", "sushi cultura", "onigiri", "mochi", "origami", "ikebana",
    "samurai", "ninja", "geisha", "manga história",
]

# Games completos
GAMES_ALL = [
    "zelda ocarina of time", "zelda breath of the wild", "super mario games",
    "sonic", "crash bandicoot", "spyro", "tomb raider", "resident evil",
    "silent hill", "final fantasy", "kingdom hearts", "nintendo", "sega",
    "atari", "playstation games", "xbox games", "pc games", "indie games",
    "stardew valley", "hollow knight", "celeste", "hades", "terraria",
    "the sims", "simcity", "cities skylines", "civilization", "age of empires",
    "total war", "hearts of iron", "eu4", "paradox games",
    "grand theft auto", "red dead redemption", "cyberpunk 2077", "witcher 3",
    "elden ring", "dark souls", "bloodborne", "sekiro", "god of war",
    "horizon zero dawn", "the last of us", "uncharted", "spider-man games",
    "batman arkham", "assassin's creed", "far cry", "watch dogs",
    "the elder scrolls", "skyrim", "fallout", "dragon age", "mass effect",
    "bioshock", "dishonored", "prey", "dead space", "doom", "quake",
    "halo", "gears of war", "destiny", "overwatch", "apex legends",
    "valorant rrs", "league of legends game", "dota 2", "cs go", "rainbow six siege",
    "fortnite game", "pubg", "call of duty", "battlefield", "titanfall",
    "minecraft game", "roblox game", "garry's mod", "half-life", "portal",
    "team fortress", "counter strike", "racing games", "fifa", "pes", "nba 2k",
    "madden", "need for speed", "forza", "gran turismo", "mario kart",
    "street fighter", "mortal kombat", "tekken", "injustice", "smash bros",
    "animal crossing", "pokemon games", "digimon", "yugioh", "magic the gathering",
    "card games", "board games", "rpg de mesa", "dungeons and dragons",
    "warhammer", "miniaturas", "escape room", "jogo de tabuleiro",
]

# Mais estilos musicais
MUSIC_STYLES = [
    "sertanejo", "pagode", "funk carioca", "trap", "hip hop", "rap", "drill",
    "reggaeton", "reggae", "ska", "dubstep", "techno", "house", "trance",
    "drum and bass", "hardstyle", "edm", "lofi", "jazz", "blues", "gospel",
    "mpb", "bossa nova", "samba", "pagode baiano", "axé", "forró", "xote",
    "baião", "frevo", "maracatu", "axé music", "arrocha", "brega",
    "brega funk", "piseiro", "garota", "vaquejada", "seresta", "bolero",
    "salsa", "merengue", "tango", "cumbia", "bachata", "mambo", "chacha",
    "sertanejo raiz", "sertanejo universitário", "modão", "raca", "gospel contemporâneo",
    "música clássica", "ópera", "sinfonia", "concerto", "sonata", "chorinho",
    "seresta", "xaxado", "samba-enredo", "samba de roda", "pagode de mesa",
]

# Instrumentos e música
INSTRUMENTS = [
    "violão", "guitarra", "baixo", "bateria", "piano", "teclado", "acordeão",
    "sanfona", "violino", "cello", "contrabaixo", "harpa", "flauta", "saxofone",
    "clarinete", "trompete", "trombone", "oboe", "fagote", "tuba", "corneta",
    "gaita", "harmônica", "viola", "cavaquinho", "banjo", "mandolim", "ukulele",
    "tambor", "conga", "bongô", "timbal", "pandeiro", "berimbau", "agogô",
    "triângulo", "chocalho", "reco-reco", "maracas", "sinos", "xilofone",
    "sitara", "tabla", "didgeridoo", "organ", "sintetizador",
]

# Fenômenos naturais e clima
PHENOMENA = [
    "raio", "trovão", "tempestade", "tornado", "furacão categoria", "ciclone",
    "tsunami", "maremoto", "terremoto", "tremor", "enchente", "inundação",
    "deslizamento", "seca", "deserto no brasil", "geada", "neve", "granizo",
    "chuva ácida", "poluição do ar", "poluição da água", "poluição sonora",
    "efeito estufa", "buraco na camada de ozônio", "mudanças climáticas",
    "aquecimento global", "fenômeno la niña", "fenômeno el niño",
    "frente fria", "frente quente", "pressão atmosférica", "unidade de medidas",
    "graus celsius", "fahrenheit", "kelvin", "umidade relativa", "índice de calor",
    "índice uv", "radiação solar", "vulcão em erupção", "lava", "magma",
    "nuvens", "tipos de nuvem", "nuvem de chuva", "nuvem cumulonimbus",
    "arco-íris", "miragem", "nebulosidade", "nevoeiro", "neblina", "vento",
    "brisa", "monção", "passado glacial", "era do gelo", "permafrost",
]

# Instituições internacionais e termos do mundo
WORLD_TERMS = [
    "onu", "unesco", "unicef", "oms", "fmi", "banco mundial", "nato", "g20",
    "g7", "opec", "uele", "mercosul", "usp dh", "tratados internacionais",
    "direitos humanos", "declaração universal dos direitos humanos", "onu mulher",
    "comissão de direitos humanos", "anistia internacional", "greenpeace",
    "organização mundial do comércio", "omc", "onu meio ambiente", "unfpa",
    "objetivos de desenvolvimento sustentável", "ods", "agenda 2030",
    "protocolo de kyoto", "acordo de paris", "cúpula do clima", "cop30",
    "geopolítica", "guerra comercial", "sancões econômicas", "embargo",
    "diplomacia", "embaixada", "consulado", "visto americano", "visto europeu",
    "green card", "imigração", "cidadania", "passaporte brasileiro", "remessa",
    "adotar gato", "leis no brasil", "constituição brasileira", "código civil brasileiro",
    "código penal brasileiro", "código do consumidor", "estatuto da criança e do adolescente",
    "eca", "estatuto do idoso", "lei trabalhista brasileira", "clt",
    "direito do trabalho", "direito penal", "direito civil", "direito tributário",
]

# Ferramentas de escritório e produtividade
OFFICE_TOOLS = [
    "word", "excel", "powerpoint", "outlook", "google docs", "google sheets",
    "google slides", "notion", "trello", "asana", "monday", "clickup",
    "slack", "teams", "zoom", "google meet", "skype", "whatsapp business",
    "canva", "figma", "photoshop", "illustrator", "premiere", "after effects",
    "audacity", "obs studio", "streamlabs", "obs", "discord server",
    "google trends", "google analytics", "seo", "sem", "google ads", "meta ads",
    "tiktok ads", "instagram ads", "email marketing", "mailchimp", "rd station",
    "hubspot", "salesforce", "zendesk", "intercom", "kera", "n8n", "zapier",
    "make", "botpress", "dialogflow", "power automate", "vba", "macro",
    "planilha de controle", "controle financeiro", "fluxo de caixa",
    "orcamento pessoal", "planilha de gastos", "dashboards", "kpi",
    "crm", "erp", "sap", "totvs", "blip", "bi", "etl",
]

# Culinária regional brasileira
REGIONAL_FOOD = [
    "churrasco gaúcho", "feijoada completa", "moqueca baiana", "vatapá",
    "acaraje", "tacaca", "tambaquí", "peixe frito", "caranguejo ucraniano",
    "pato no tucupi", "maniçoba", "baião de dois", "cuscuz nordestino",
    "bode guisado", "buchada", "tropeiro", "pão de queijo mineiro",
    "feijão tropeiro", "frango com quiabo", "leitao à pururuca", "virado à paulista",
    "bobó de camarão", "caldeirada", "moqueca capixaba", "feijão verde",
    "canjiquinha", "angu", "polenta", "toscana", "galinha caipira",
    "pernil com farofa", "lombo com farofa", "arroz carreteiro", "paçoca de carne",
    "farinha de mandioca", "tapioca recheada", "beiju", "cuscuz de milho",
    "mingau", "bolo de fubá", "broa de milho", "pamonha doce", "canjica",
    "curau", "pudim de leite", "manjar", "brigadeiro gourmet", "beijinho",
    "cajuzinho", "olho de sogra", "quindim", "marmelada", "goiabada",
    "rapadura", "melado", "queijo minas", "requeijão", "manteiga de garrafa",
]

# Física e ciências do cotidiano
EVERYDAY_SCIENCE = [
    "gravidade", "magnetismo", "eletricidade", "corrente elétrica", "voltagem",
    "amperagem", "resistência elétrica", "circuito elétrico", "campo magnético",
    "ímã", "eletromagnetismo", "termodinâmica", "calor", "temperatura",
    "pressão", "vapor", "condensação", "evaporação", "ebulição", "fusão",
    "solidificação", "sublimação", "densidade", "massa", "peso", "volume",
    "velocidade", "aceleração", "força", "energia", "energia cinética",
    "energia potencial", "energia química", "trabalho", "potência",
    "leis de newton", "lei da gravitação", "terceira lei", "movimento",
    "ondas", "som", "luz", "refração", "reflexão", "prisma", "lente",
    "microscópio", "telescópio", "espelho", "raio laser", "raios x",
    "fungos", "algas", "protozoários", "bactérias benéficas", "liberação de energia",
    "reação química", "molécula", "átomo", "elemento químico", "tabela periódica",
    "metais", "não metais", "gases nobres", "sais", "ácidos", "bases",
    "ph", "solução", "mistura", "suspensão", "colóide", "precipitação",
]

# Artistas visuais e designers
VISUAL_ARTISTS = [
    "pablo picasso", "van gogh", "monet", "renoir", "degas", "cézanne",
    "auguste rodin", "michelangelo", "da vinci", "rafael sanzio",
    "botticelli", "candido portinari", "tarsila do amaral", "diego rivera",
    "frida kahlo", "salvador dali", "andy warhol", "banksy", "jean-michel basquiat",
    "keith haring", "roy lichtenstein", "edvard munch", "gustav klimt",
    "johannes vermeer", "rembrandt", "caravaggio", "goya", "henri matisse",
    "paul gauguin", "paul klee", "wassily kandinsky", "piet mondrian",
    "umbra banco", "lívia melzi", "binho", "os gemeos", "nina pandolfo",
    "cobrança de arte", "grafite", "muralismo", "instalação artística",
    "performance art", "fotografia de rua", "street art", "arte abstrata",
    "arte moderna", "arte contemporânea", "impressionismo", "cubismo",
    "surrealismo", "expressionismo", "pop art", "fauvismo", "dadaísmo",
    "barroco", "renascimento", "neoclassicismo", "romantismo", "art deco",
    "fotografia", "desenho artístico", "aquarela", "guache", "óleo sobre tela",
    "escultura", "cerâmica artística", "design gráfico", "diagramação",
]

#############################################################
# FRENTE 2 (rumo a 90 mil buscas)
#############################################################

# Países: bandeiras, economia, cultura, curiosidades
COUNTRIES_DETAIL = [
    "brasil hoje", "economia do brasil", "cultura do brasil", "história do brasil",
    "política do brasil", "população do brasil", "clima do brasil", "relevo do brasil",
    "bandeira do brasil", "hino do brasil", "moeda do brasil",
    "argentina banif", "cultura da argentina", "economia da argentina", "população da argentina",
    "bandeira do méxico", "cultura do méxico", "economia do méxico", "história do méxico",
    "bandeira da frança", "cultura da frança", "economia da frança", "história da frança",
    "bandeira dos estados unidos", "cultura dos estados unidos", "economia dos estados unidos",
    "bandeira do japão", "cultura do japão", "economia do japão", "história do japão",
    "bandeira da alemanha", "cultura da alemanha", "economia da alemanha",
    "bandeira da itália", "cultura da itália", "comida italiana",
    "bandeira da espanha", "cultura da espanha", "história da espanha",
    "bandeira da inglaterra", "cultura da inglaterra", "economia da inglaterra",
    "bandeira do canadá", "cultura do canadá", "bandeira da rússia",
    "bandeira da china", "cultura da china", "economia da china", "história da china",
    "bandeira da índia", "cultura da índia", "economia da índia",
    "bandeira da coréia do sul", "cultura da coréia do sul", "economia da coréia do sul",
    "bandeira da austrália", "cultura da austrália", "bandeira do chile",
    "bandeira de portugal", "cultura de portugal", "história de portugal",
    "bandeira da grécia", "cultura da grécia", "história da grécia antiga",
    "bandeira de israel", "cultura de israel", "bandeira da turquia",
    "bandeira da suíça", "bandeira da suécia", "bandeira da noruega",
    "bandeira da dinamarca", "bandeira da finlândia", "bandeira da polônia",
    "bandeira da ucrânia", "bandeira do egito", "cultura do egito", "história do egito",
    "bandeira da nigéria", "bandeira de marrocos", "bandeira de angola",
    "bandeira de moçambique", "bandeira da venezuela", "bandeira do peru",
    "bandeira da colômbia", "bandeira do uruguai", "bandeira do paraguai",
    "bandeira da bélgica", "bandeira da holanda", "bandeira da Áustria",
    "bandeira da república tcheca", "bandeira da romênia", "bandeira da hungria",
    "bandeira da bulgária", "bandeira da croácia", "bandeira da sérvia",
    "bandeira da nova zelândia", "bandeira das filipinas", "bandeira do vietnã",
    "bandeira da tailândia", "bandeira da indonésia", "bandeira da malásia",
    "bandeira da singapura", "bandeira do canada", "bandeira do paquistão",
    "bandeira do bangladesh", "bandeira da africa do sul", "população da africa do sul",
]

# Cidades do mundo (mais)
CITIES_WORLD = [
    "nova york", "los angeles", "chicago", "houston", "phoenix", "philadelphia",
    "san francisco", "seattle", "boston", "miami", "atlanta", "dallas", "denver",
    "londres", "paris", "roma", "madrid", "berlim", "moscou", "istambul",
    "pequim", "xangai", "shenzhen", "guangzhou", "hong kong", "toquio",
    "osaka", "kyoto", "seul", "busan", "singapura", "bangcoc", "jacarta",
    "manila", "hanoi", "cidade de ho chi minh", "cairo", "lagos", "nairobi",
    "nairóbi", "cidade do cabo", "johannesburg", "casablanca", "túnis",
    "dacar", "acra", "adoris abeba", "dar es salaam", "cartum", "kigali",
    "lusaka", "harare", "maputo", "luanda", "sydney", "melbourne", "perth",
    "auckland", "wellington", "montreal", "toronto", "ottawa", "vancouver",
    "cidade do méxico", "guadalajara", "monterrey", "bogotá", "medellin",
    "lima", "arequipa", "santiago", "valparaíso", "buenos aires", "rosario",
    "montevidéu", "assunção", "caraças", "lima", "quito", "la paz", "sucre",
    "brasília", "são paulo capital", "rio de janeiro capital", "salvador capital",
    "porto", "lisboa capital", "paris capital", "roma capital", "madri capital",
]

# Culinária / comidas do mundo (mais nuances)
FOOD_MORE = [
    "risoto", "polenta", "risco", "feijão tropeiro", "moqueca", "feijoada completa",
    "carne de panela", "strogonoff", "lasanha", "escondidinho", "fajita", "tacos",
    "burrito", "guacamole", "ceviche", "lomo saltado", "arepa", "empanada",
    "tamale", "pozole", "chilaquiles", "mole", "chimichanga", "quesadilla",
    "nacho", "churrasco argentino", "asado", "milanesa", "pastel de carne",
    "humitas", "locro", "arroz con pollo", "feijão preto", "tutu", "angú",
    "galinhada", "empadão", "escondidinho de carne seca", "baião de dois",
    "vatapá", "caruru", "acarajé", "moqueca de peixe", "moqueca de camarão",
    "cabidela", "feijão verde", "caldo de cana", "açaí", "cupuaçu",
    "bacuri", "graviola", "cajá", "jabuticaba", "pitanga", "seriguela",
    "caju", "pequi", "umbu", "murici", "açaí na tigela", "tapioca",
    "beiju", "cuscuz", "cuscuz paulista", "pão de queijo", "broa",
    "quindim", "pudim", "manjar", "doce de leite", "brigadeiro", "beijinho",
    "cajuzinho", "olho de sogra", "merengue", "sagu", "ambrosia", "arroz doce",
]

# Plantas, árvores e horta
PLANTS = [
    "rosa", "orquídea", "girassol", "tulipa", "margarida", "lírio", "hortênsia",
    "lavanda", "jasmim", "gardênia", "violeta", "petúnia", "begônia", "azaleia",
    "camélia", "dália", "gladíolo", "antúrio", "bromélia", "cacto", "suculenta",
    "babosa", "aloe vera", "hortelã", "manjericão", "alecrim", "tomilho",
    "sálvia", "orégano", "coentro", "salsa", "cebolinha", "louro", "funcho",
    "eucalipto", "pinheiro", "carvalho", "bordo", "ipê", "pau-brasil",
    "jacarandá", "mangueira", "laranjeira", "limoeiro", "pessegueiro",
    "macieira", "pereira", "videira", "cafeeiro", "cacaueiro", "dendezeiro",
    "palmeira", "juçara", "açaizeiro", "bananeira", "abacateiro", "goiabeira",
    "mamoeiro", "meloeiro", "melancia", "abacaxi", "morango", "framboesa",
    "amora", "mirtilo", "kiwi", "uva", "figo", "romã", "manga", "pêssego",
    "ameixa", "cereja", "noz", "amêndoa", "avelã", "castanha", "pistache",
    "horta orgânica", "plantar em vaso", "adubo", "compostagem", "poda",
    "irrigação", "pragas de jardim", "paisagismo", "jardinagem vertical",
]

# Profissões e áreas de atuação
PROFESSIONS = [
    "médico", "enfermeiro", "dentista", "farmacêutico", "psicólogo", "psiquiatra",
    "advogado", "juiz", "promotor", "delegado", "policial", "bombeiro",
    "engenheiro civil", "engenheiro elétrico", "engenheiro mecânico", "engenheiro de software",
    "arquiteto", "urbanista", "designer", "designer de interiores", "ilustrador",
    "fotógrafo", "cinegrafista", "editor de vídeo", "músico", "cantor", "compositor",
    "ator", "atriz", "diretor de cinema", "roteirista", "jornalista", "repórter",
    "editor", "escritor", "poeta", "tradutor", "intérprete", "professor",
    "pedagogo", "diretor de escola", "coordenador pedagógico", "bibliotecário",
    "contador", "auditor", "economista", "administrador", "gestor", "analista financeiro",
    "analista de marketing", "publicitário", "social media", "copywriter", "seo",
    "vendedor", "representante comercial", "corretor de imóveis", "corretor de seguros",
    "motorista", "taxista", "caminhoneiro", "piloto", "comissário de bordo",
    "garçom", "cozinheiro", "chef de cozinha", "padeiro", "açougueiro",
    "cabeleireiro", "barbeiro", "manicure", "pedicure", "maquiador", "estilista",
    "costureiro", "alfaiate", "joalheiro", "relojoeiro", "ourives",
    "eletricista", "encanador", "pedreiro", "carpinteiro", "marceneiro",
    "pintor", "serralheiro", "mecânico", "mecânico de automóveis", "pneu", "chaveiro",
    "agricultor", "pecuarista", "pescador", "apicultor", "veterinário",
    "explore", "astronauta", "astrólogo", "geógrafo", "biólogo", "químico", "físico",
    "matemático", "estatístico", "programador", "desenvolvedor", "analista de sistemas",
    "administrador de banco de dados", "cientista de dados", "engenheiro de dados",
    "segurança da informação", "pentester", "hacker ético", "suporte técnico",
]

# Esportes e times (mais)
SPORTS_GLOB = [
    "flamengo", "corinthians", "são paulo", "palmeiras", "grêmio", "internacional de porto alegre",
    "cruzeiro", "atlético mineiro", "vasco da gama", "botafogo", "fluminense", "santos fc",
    "flamengo 2019", "palmeiras 2020", "são paulo tricampeão", "corinthians mundial",
    "gremio libertadores", "cruzeiro brasileirão", "vasco expresso da vitória",
    "real madrid", "barcelona", "atlético de madrid", "sevilla", "betis", "valencia",
    "manchester united", "manchester city", "liverpool", "chelsea", "arsenal", "tottenham",
    "newcastle", "west ham", "everton", "leeds", "psg", "marseille", "lyon", "monaco",
    "lille", "nice", "bayern de munique", "borussia dortmund", "rb leipzig", "bayer leverkusen",
    "schalke", "werder bremen", "juventus", "inter de milão", "milão", "napoli", "roma fc",
    "lazio", "atalanta", "fiorentina", "torino", "porto", "benfica", "sporting lisboa",
    "braga", "ajax", "psv", "feyenoord", "celtic", "rangers", "galatasaray", "fenerbahce",
    "boca juniors", "river plate", "independiente", "racing", "san lorenzo", "peñarol",
    "nacional", "flamengo do uruguai", "cerro porteño", "colômbia seleção",
    "seleção argentina", "seleção da alemanha", "seleção da frança", "seleção da espanha",
    "seleção da itália", "seleção da inglaterra", "seleção de portugal", "seleção do belga",
    "seleção holandesa", "seleção croata", "seleção uruguaia", "seleção chilena",
    "seleção colombiana", "seleção peruana", "seleção paraguaia", "seleção equatoriana",
    "eurocopa 2024", "copa do mundo 2026", "copa américa 2024", "libertadores 2024",
    "brasileirão série a", "brasileirão série b", "copas do brasil", "mundial de clubes",
    "fifa world cup", "uefa champions league", "eu paulo champions league",
]

# Carros, motos e transporte
VEHICLES = [
    "carro elétrico", "carro híbrido", "carro a gasolina", "carro a diesel",
    "carro flex", "carro popular", "carro de luxo", "carro esportivo",
    "ferrari", "lamborghini", "porsche", "bugatti", "maserati", "rolls royce",
    "tesla", "tesla model 3", "toyota", "corolla", "hilux", "civic", "golf",
    "fusca", "brasilia", "opala", "chevette", "kombi", "gol", "onix", "kwid",
    "hb20", "argo", "mobi", "uno", "palio", "corsa", "astra", "vectra",
    "fiesta", "focus", "ecosport", "kuga", "ranger", "s10", "ram", "jimmy",
    "bike", "bicicleta", "bicicleta elétrica", "scooter", "patinete elétrico",
    "moto", "moto 125", "moto 250", "sport bike", "naked", "custom", "touring",
    "honda", "yamaha", "suzuki", "kawasaki", "ducati", "bmw moto", "harley",
    "caminhão", "ônibus", "ônibus elétrico", "metrô", "trem", "vlt", "brt",
    "trem de alta velocidade", "bonde", "aeroporto", "avião", "avião comercial",
    "jato", "helicóptero", "drone", "barco", "iate", "navio", "cruzeiro marítimo",
    "ferry", "catamarã", "submarino", "navio cargueiro", "trem turístico",
]

# Tecnologia: software, empresas, apps
TECH_APPS = [
    "facebook", "instagram", "whatsapp", "youtube", "tiktok", "snapchat",
    "telegram", "discord", "reddit", "twitch", "pinterest", "linkedin",
    "x (twitter)", "threads", "bluesky", "mastodon", "signal", "wechat",
    "spotify", "apple music", "deezer", "soundcloud", "amazon prime music",
    "netflix", "disney plus", "hbo max", "prime video", "apple tv plus",
    "paramount plus", "star plus", "globoplay", "vivo play", "youtube premium",
    "google", "google maps", "google translate", "google lens", "google photos",
    "gmail", "outlook", "icloud", "onedrive", "dropbox", "mega", "mediafire",
    "notion", "obsidian", "roam", "evernote", "simplenote", "google keep",
    "wordpress", "shopify", "woocommerce", "magazine luiza marketplace",
    "amazon seller", "mercado livre", "shopee", "shein", "alibaba", "aliexpress",
    "steam", "epic games", "xbox game pass", "playstation plus", "nintendo online",
    "gog", "itch.io", "roblox studio", "minecraft server", "twitch prime",
    "chrome", "firefox", "safari", "edge", "opera", "brave", "vivaldi",
    "windows", "mac os", "linux mint", "ubuntu", "fedora", "android", "ios",
]

# História: eventos e períodos
HISTORY_EVENTS = [
    "revolução francesa", "revolução russa", "queda do muro de berlim",
    "guerra do vietnã", "guerra da coreia", "guerra do golfo", "guerra da ucrânia",
    "guerra de canudos", "revolução de 30", "revolução de 32", "revolta constitucionalista",
    "proclamação da república", "independência da argentina", "independência da colômbia",
    "independência do méxico", "independência dos estados unidos", "primeira república",
    "república velha", "era vargas", "golpe de 1964", "direta já", "plano collor",
    "crise de 1929", "crise de 2008", "pandemia de covid", "praga covid",
    "guerra dos cem anos", "guerra das rosas", "guerras púnicas", "guerras médicas",
    "império otomano", "império austro-húngaro", "império russo", "império japonês",
    "bizâncio", "império inca", "império asteca", "império maia", "civilização maia",
    "civilização asteca", "civilização inca", "civilização egípcia", "povos indígenas do brasil",
    "tupis", "guaranis", "ianomâmis", "xavantes", "xingu", "kraft", "cunhã",
    "aldeias indígenas", "reserva indígena", "língua tupi", "língua guarani",
    "scrambler para africa", "era das descobertas", "grandes navegações",
    "tratado de tordesilhas", "tratado de madri", "tratado de petrópolis",
    "tratado de versalhes", "liga das nações", "onu história", "guerra fria fases",
    "corrida espacial", "missão apollo 11", "pouso na lua", "primeiro satélite",
    "esputnik", "internacional espacial", "estação espacial internacional",
]

# Filosofia e pensadores (mais)
PHILOSOPHERS = [
    "sócrates", "platão", "aristóteles", "epicuro", "zenão de cítio", "sêneca",
    "cicerón", "marco aurélio", "agostinho", "tomás de aquino", "descartes",
    "locke", "hume", "kant", "hegel", "schopenhauer", "nietzsche", "kierkegaard",
    "marx", "engels", "weber", "durkheim", "comte", "spencer", "bergson",
    "russell", "wittgenstein", "heidegger", "sartre", "camus", "de beauvoir",
    "foucault", "derrida", "deleuze", "guattari", "zizek", "badiou",
    "nietzsche ala", "ética e moral", "justiça social", "liberdade", "igualdade",
    "verdade", "bem e mal", "finalidade da vida", "sentido da vida",
    "teoria do conhecimento", "lógica formal", "argumento", "falácias",
    "pensamento crítico", "questionamento", "dúvida", "certeza", "crença",
]

# Astrologia e esoterismo
ASTROLOGY = [
    "astrologia", "signos", "signo de áries", "signo de touro", "signo de gêmeos",
    "signo de câncer", "signo de leão", "signo de virgem", "signo de libra",
    "signo de escorpião", "signo de sagitário", "signo de capricórnio",
    "signo de aquário", "signo de peixes", "ascendente", "mapa astral",
    "mapa astral grátis", "casa astrológica", "planetas no mapa", "lua no signo",
    "horóscopo do dia", "horóscopo semanal", "horóscopo do amor", "horóscopo do trabalho",
    "tarot", "tarot do amor", "cartas do tarot", "tiragem de tarot", "oráculo",
    "numerologia", "número da sorte", "cristais", "significado das pedras",
    "energia positiva", "leis da atração", "pensamento positivo", "meditação",
    "chakras", "reiki", "baralho cigano", "runas", "significado dos sonhos",
    "sonhar com água", "sonhar com cobra", "sonhar com dente", "sonhar com gato",
    "sonhar com cachorro", "sonhar com belo", "sonhar com morte", "sonhar com bebê",
    "sonhos repetidos", "sonho lúcido", "premonição",
]

# Saúde mental e bem-estar
WELLNESS = [
    "ansiedade", "depressão", "estresse", "burnout", "insônia", "síndrome do pânico",
    "overthinking", "memória", "concentração", "foco", "procrastinação",
    "estabelecer rotina", "higiene do sono", "qualidade do sono", "sono profundo",
    "alimentação emocional", "autocuidado", "terapia", "psicoterapia", "cognitivo comportamental",
    "mindfulness", "respiração", "exercício respiratório", "relaxamento", "alongamento",
    "ioga", "meditação guiada", "banho de sol", "vitamina d", "atividade física",
    "caminhada", "corrida leve", "musculação", "funcional", "crossfit", "pilates",
    "equilíbrio", "postura", "dor nas costas", "dor no pescoço", "dormência",
    "rotina da manhã", "rotina da noite", "hidratação", "água", "saudável",
    "comer bem", "dieta balanceada", "jejum intermitente", "alimentação", "nutricionista",
    "meta de emagrecer", "ganhar massa", "perder barriga", "definição",
    "equilíbrio emocional", "gratidão", "positividade", "autoestima", "confiança",
]

# Internet e redes sociais (termos)
INTERNET_TERMS = [
    "viralizar", "trend", "challenge", "desafio", "fyp", "for you", "tiktok trends",
    "reels", "shorts", "stories", "live", "stream", "clipe", "memes",
    "influencer", "creator", "conteúdo", "engajamento", "algoritmo", "alcance",
    "impressões", "visualizações", "curtidas", "comentários", "compartilhamentos",
    "seguranças", "perfil", "bio", "hashtags", "trending topic", "viral",
    "seguidores", "seguir", "amigo virtual", "chat", "mensagens", "grupos",
    "comunidade", "fórum", "moderador", "admin", "ban", "block", "mute",
    "privacidade", "dados pessoais", "termos de uso", "política de privacidade",
    "cookies", "rastreamento", "algoritmo de recomendação", "feed", "tendência",
    "notificação", "push", "salvos", "favoritos", "seguir hashtag",
]

# Educação: matérias e conteúdos
SCHOOL_SUBJECTS = [
    "matemática", "português", "inglês", "espanhol", "francês", "alemão", "italiano",
    "história", "geografia", "ciências", "biologia", "física", "química", "filosofia",
    "sociologia", "arte", "música", "educação física", "redação", "gramática",
    "literatura", "clássicos da literatura", "modernismo", "romantismo", "barroco",
    "realismo", "naturalismo", "parnasianismo", "simbolismo", "pré-modernismo",
    "conto de fadas", "fábulas", "poesia", "romance", "crônica", "ensaio",
    "teatro", "drama", "comédia", "tragédia", "epopéia", "saga",
    "álgebra", "geometria", "trigonometria", "cálculo", "funções", "equações",
    "porcentagem", "frações", "dividir", "multiplicar", "adicionar", "subtrair",
    "teorema de pitágoras", "bhaskara", "regra de três", "probabilidade",
    "estatística", "gráficos", "tabelas", "medidas", "unidades de medida",
    "sistema métrico", "km", "metros", "litros", "gramas", "segundos",
]

# Tecnologia da informação (mais)
IT_TOPICS = [
    "hardware", "placa-mãe", "processador", "gpu", "memória ram", "armazenamento",
    "ssd nvme", "hd", "placa de vídeo", "fonte", "gabinete", "cooler", "ventoinha",
    "teclado", "mouse", "monitor", "cabo", "hub usb", "rota", "switch", "modem",
    "roteador wifi", "rede", "ethernet", "fibra óptica", "rede 5g", "wi-fi 6",
    "bluetooth", "nfc", "usb-c", "hdmi", "displayport", "vga", "rj45",
    "sistema operacional", "kernel", "driver", "bios", "uefi", "boot",
    "processo", "thread", "memória", "cachê", "registradores", "arquitetura",
    "linguagem de programação", "compilador", "interpretador", "depurador",
    "ide", "editor de código", "terminal", "cli", "versão", "git", "github",
    "código", "função", "classe", "objeto", "variável", "laço", "condicional",
    "api", "sdk", "framework", "biblioteca", "pacote", "dependência",
    "banco de dados", "sql", "no sql", "tabelas", "índices", "consulta",
    "frontend", "backend", "fullstack", "devops", "cloud", "aws", "azure",
    "gcp", "servidor", "container", "kubernetes", "docker", "vm",
]

# Matemática e formação (mais profundidade)
MATH_OP = [
    "equação do primeiro grau", "equação do segundo grau", "sistema de equações",
    "função linear", "função quadrática", "exponencial", "logaritmo", "seno",
    "cosseno", "tangente", "radiano", "grau", "triângulo", "quadrado", "retângulo",
    "círculo", "circunferência", "esfera", "cilindro", "cone", "pirâmide", "prisma",
    "perímetro", "área", "volume", "diagonal", "hipotenusa", "cateto",
    "números primos", "números pares", "números ímpares", "racionais", "irracionais",
    "naturais", "inteiros", "reais", "complexos", "conjuntos", "subconjuntos",
    "união", "interseção", "diferença", "produto cartesiano", "função injetora",
    "sobrejetora", "bijetora", "limite", "derivada", "integral", "somatório",
    "fatorial", "combinação", "permutação", "arranjo", "progressão", "pa", "pg",
    "matriz", "determinante", "inversa", "vetor", "escalar", "produto escalar",
    "produto vetorial", "gradiente", "divergência", "rotacional",
]

# Geografia: rios, relevo, clima do mundo
GEOG_MORE = [
    "rios do brasil", "rio amazonas afluentes", "rio são francisco", "rio tietê",
    "rio paraná", "rio iguaçu", "rio negro", "rio xingu", "rio tocantins",
    "rio madeira", "rio tapajós", "rio paraná", "rio paraguai", "rio uruguai",
    "maiores rios do mundo", "rio nilo comprimento", "rio amazonas comprimento",
    "rio mississipi", "rio yukon", "rio danúbio", "rio ren", "rio tâmisa",
    "rio sena", "rio tigre", "rio eufrates", "rio ganges sagrado",
    "maiores lagos do mundo", "lago vitória", "lago superior", "lago cáspio",
    "mar morto altitude", "lago titicaca", "lago de constança",
    "cordilheira dos andes", "alpes", "himalaia", "monte everest", "k2",
    "montes uráis", "montes rochosos", "planalto central", "serra do mar",
    "serra da mantiqueira", "chapada diamantina", "chapada dos veadeiros",
    "catacumbas", "grutas", "cavernas", "caverna azul", "dunas", "lagoa",
    "pântanos", "manguezal", "restinga", "parque nacional", "unidade de conservação",
    "bioma", "biomas do brasil", "amazônia", "cerrado", "caatinga", "pampa",
    "mata atlântica", "pantanal", "floresta tropical", "floresta temperada",
    "tundra", "taiga", "savana", "estepe", "deserto", "floresta de coníferas",
]

# Mais animais (marinhos, insetos, aves, répteis)
ANIMALS_MORE = [
    "tubarão branco", "tubarão martelo", "baleia azul", "orca", "golfinho nariz-de-garrafa",
    "vaca marinha", "foca", "leão-marinho", "morsa", "pinguim imperador",
    "polvo", "lula gigante", "caranguejo", "camarão", "lagosta", "caracol",
    "estrela-do-mar", "ouriço-do-mar", "coral", "água-viva", "cavalo-marinho",
    "peixe-palhaço", "peixe-betta", "salmão", "atum", "bacalhau", "espadarte",
    "enguia", "moreia", "arraia", "tubarão-baleia", "peixe-dourado", "tilápia",
    "piranha", "arapaima", "pirarucu", "tambaqui", "peixe-elétrico", "bagre",
    "formiga", "abelha", "vespa", "mosquito", "mosca", "besouro", "joaninha",
    "borboleta", "mariposa", "gafanhoto", "grilo", "libélula", "cigarra",
    "louva-a-deus", "escorpião", "aranha", "aranha-caranguejeira", "tarântula",
    "carrapato", "piolho", "pulga", "percevejo", "cupim", "barata", "traca",
    "escorpião", "centopeia", "milípede", "lagarta", "casulo", "pupa",
    "beija-flor", "águia-real", "coruja-buraqueira", "papagaio-verdadeiro",
    "tucano", "arara-canindé", "arara-vermelha", "carcará", "falconete",
    "pombo", "pardal", "sabiá", "joão-de-barro", "canário-da-terra",
    "bem-te-vi", "sanguessuga", "minhoca", "caramujo", "lesma", "pernilongo",
    "zangão", "marcassita", "cavalo-marinho", "camaleão", "iguana-verde",
    "jacaré-do-pantanal", "crocodilo-do-nilo", "tartaruga-marinha", "cágado",
    "jabuti-piranga", "cobra-coral", "jararaca", "tamanduá-bandeira",
    "tatu-galinha", "capivara", "onça-pintada", "jaguatirica", "puma",
    "lobo-guará", "ariranha", "peixe-boi", "golfinho-rosa", "boto-cor-de-rosa",
    "macaco-prego", "muriqui", "sagui", "mico-leão-dourado", "preguiça",
]

# Personagens de ficção e quadrinhos/disney
FICTION_CHARS = [
    "superman", "batman", "mulher maravilha", "aquaman", "flash", "lanterna verde",
    "ciborgue", "homem-aranha", "hulk", "thor", "capitão américa", "homem de ferro",
    "viúva negra", "gavião arqueiro", "pantera negra", "doutor estranho",
    "capitão marvel", "wanda", "visão", "mirage", "loki", "deadpool",
    "wolverine", "x-men", "magneto", "professor x", "gambit", "jubileu",
    "venom", "carnificina", "duende verde", "doutor octopus", "sandman",
    "mago", "homem-aranha no multiverso", "liga da justiça", "vingadores",
    "justiceiro", "demolidor", "luke cage", "cavaleiro da lua",
    "hercules", "perseu", "zeus", "poseidon", "hades", "atena", "apolo",
    "ares", "hermes", "dionísio", "hêmis", "deuses gregos", "deuses egípcios",
    "rá", "osíris", "ísis", "hórus", "anúbis", "set", "deusa nut",
    "deuses nórdicos", "odin", "thor nórdico", "loki nórdico", "freya",
    "valquírias", "valhalla", "ragnarok", "asgard",
    "mickey mouse", "minnie", "pateta", "pato donald", "huguinho", "zézinho",
    "lusinha", "margarida", "pluto", "tio patinhas", "gastão", "pateta",
    "mundinho", "cascão", "magali", "cebolinha", "monica e cebolinha",
    "turma da mônica", "mônica joven", "papelete", "jovem guarda",
    "scooby-doo", "salsicha", "velma", "fred", "daphne", "os simpsons",
    "homer simpson", "marge", "bart", "lisa", "maggie", "south park",
    "cartman", "kenny", "stan", "kyle", "family guy", "peter griffin",
    "rick and morty", "rick sanchez", "morty", "beth", "jerry",
]

# Esportes que não são futebol (times e atletas)
SPORTS_NOTFOOT = [
    "nba", "nfl", "mlb", "nhl", "nba draft", "jordan", "lebrôn", "kobe bryant",
    "magic johnson", "larry bird", "shaquille o'neal", "stephen curry",
    "kevin durant", "giannis", "jokic", "luka doncic", "curry", "westbrook",
    "basquete feminino", "futebol americano", "quarterback", "tom brady",
    "patrick mahomes", "aaron rodgers", "joe montana", "peyton manning",
    "beisebol", "home run", "yankees", "red sox", "perfeit game",
    "hóquei no gelo", "patinagem", "wayne gretzky", "penguins", "david nacka",
    "fórmula 1", "hamilton", "verstappen", "leclerc", "ferrari f1",
    "mclaren", "red bull f1", "mercedes f1", "vettel", "alonso", "senna",
    "ayrton senna", "prost", "piquet", "massa", "bottas", "ricciardo",
    "motogp", "valentino rossi", "marc marduez", "neto", "dovizioso",
    "tênis", "nadal", "federer", "djokovic", "serena williams", "garbiñe",
    "rafael nadal", "auus open", "roland garros", "wimbledon", "us open",
    "boxe", "muhammad ali", "mike tyson", "floyd mayweather", "canelo",
    "migguel cotto", "ufc", "mcgregor", "khabib", "islam", "jon jones",
    "golfe", "tiger woods", "jack nicklaus", "masters", "xadrez", "carlsen",
    "kasparov", "karpov", "maia", "xadrez online", "e-sports", "counter strike",
    "league of legends mundial", "valorant champions", "dota ti", "gams",
    "skate", "tony hawk", "surfe", "gabriel medina", "tico", "filipe toledo",
    "atletismo", "100 metros", "usain bolt", "maratona", "pacing",
    "ciclismo", "tour de france", "pogacar", "ciclismo de estrada",
]

# Pessoas famosas (mais)
FAMOUS_PEOPLE = [
    "marie curie", "albert einstein biografia", "isaac newton biografia",
    "stephen hawking biografia", "charles darwin biografia", "nikola tesla biografia",
    "thomas edison biografia", "galileu biografia", "johannes kepler",
    "frederico nietzsche", "carlos drummond", "clarice lispector", "jorge amado",
    "guimarães rosa", "machado de assis vida", "machado de assis obras",
    "carlos drummond poemas", "fernando pessoa", "josé saramago", "gabriel garcía márquez",
    "mario vargas llosa", "pablo neruda", "octavio paz", "jorge luis borges",
    "julio cortázar", "víctor hugo", "leon tolstoi", "fiódor dostoiévski",
    "franz kafka", "james joyce", "virginia woolf", "william shakespeare",
    "george orwell", "jane austen", "charles dickens", "mark twain",
    "ernest hemingway", "f. scott fitzgerald", "j.r.r. tolkien", "c.s. lewis",
    "j.k. rowling", "stephen king", "paulo coelho", "machado de assis biografia",
    "flor de lis", "dom quixote autor", "cervantes", "dan brown", "suzanne collins",
    "sir arthur conan doyle", "agatha christie", "sófocles", "eurípides",
    "averrois", "avicena", "george washington", "abraham lincoln", "winston churchill",
    "roosevelt", "kennedy", "reagan", "queen elizabeth", "rainha victoria",
    "napoleão bonaparte", "catherine a grande", "nefertiti", "cleópatra biografia",
    "pablo escobar", "che guevara", "fidel castro", "perón", "evita perón",
    "salvador allende", "simón bolívar", "jose martir", "mao tsé-tung",
    "deng xiaoping", "chien", "gandhi vida", "madre teresa", "joana d'arc",
    "cristóvão colombo", "vasco da gama", "pedro alvares cabral", "magalhães",
]

# Lazer e hobbies
LEISURE = [
    "leitura", "ler livros", "dicas de leitura", "clube do livro", "biblioteca",
    "fanfic", "mangá brasil", "quadrinhos brasileiros", "graphic novel",
    "artesanato", "crochê", "tricô", "bordado", "ponto cruz", "macramê",
    "cerâmica", "pintura em tela", "desenho", "aquarela", "scrapbook",
    "jardinagem", "aquário", "terrário", "kokedama", "bonsai", "pets",
    "cachorros de estimação", "gatos de estimação", "ração", "passeio com pet",
    "caça-palavras", "palavras cruzadas", "sudoku", "xadrez", "dominó",
    "damas", "truco", "poker", "buraco", "baralho", "uno", "jenga",
    "festas", "aniversário", "festa junina", "festa infantil", "churrasco",
    "piquenique", "acampamento", "caminhada", "trilha", "touring de bike",
    "rodovia", "viagem de carro", "viajar sozinho", "viajar em grupo",
    "mochilão", "voluntariado", "fotografia de natureza", "fotografia de rua",
    "vídeo game", "fazer streaming", "assistir séries", "maratonar", "binge",
    "cozinhar", "receitas fáceis", "confeitaria", "pão caseiro", "fermentação",
    "instrumento musical", "compor música", "cantar", "karaokê",
    "dança", "dançar", "forró", "samba", "balé", "hip hop dança",
    "fitness", "academia", "correr", "caminhar", "alongamento", "meditação",
    "ioga", "jogos de tabuleiro", "jogos de cartas", "rpg de mesa", "larp",
    "colecionismo", "figurinhas", "cromos", "bonecos", "action figures",
]

# Astronomia: objetos e exploração
ASTRONOMY_OBJ = [
    "sol", "lua", "marte", "júpiter", "saturno", "urano", "netuno", "mercúrio", "vênus",
    "planeta terrestre", "planeta gasoso", "planeta anão", "ceres", "égea",
    "luas de júpiter", "luas de saturno", "anel de saturno", "titan", "europa",
    "ganímedes", "calisto", "encélado", "io", "fobos", "deimos",
    "estrelas", "estrelas do mar", "estrelas cadentes", "constelação zodiacal",
    "astros", "via láctea galáxia", "universo", "multiverso", "cosmos",
    "expansão do universo", "velocidade da luz", "ano-luz", "parsec",
    "exoplaneta", "sistema solar planetas", "kuiper", "nuvem de oort",
    "cometa halley", "cometa neowise", "meteorito brasil", "chuva de meteoros",
    "eclipse anular", "trânsito", "ocultação", "conjunção planetária",
    "satélite natural", "satélite artificial", "estação espacial", "iss",
    "telescópio hubble", "telescópio james webb", "voyager", "new horizons",
    "mars rover", "curiosity", "perseverance", "sondas espaciais", "foguete",
    "spacex", "falcon", "starship", "nasa", "esa", "jaxa", "shenzhou",
    "lançamento espacial", "óvbit", "astronauta", "traje espacial",
    "gravidade do espaço", "vida no espaço", "markwatney",
]

# Ciência moderna (mais)
MODERN_SCI = [
    "inteligência artificial", "machine learning", "deep learning", "redes neurais",
    "visão computacional", "processamento de linguagem natural", "nlp",
    "chatbot", "assistente virtual", "reconhecimento de voz", "síntese de voz",
    "robótica", "automação robotizada", "robot humanoide", "braço robótico",
    "drones", "veículos autônomos", "carro autônomo", "piloto automático",
    "biologia sintética", "edição genética", "crispr", "dna edição",
    "genoma humano", "sequenciamento genético", "clonagem", "células-tronco",
    "biotecnologia", "nanotecnologia", "nanomateriais", "grafeno",
    "materiais avançados", "supercondutor", "supercondutividade",
    "energia de fusão", "reator de fusão", "energia nuclear segura",
    "bateria de estado sólido", "bateria de lítio", "hidrogênio verde",
    "captura de carbono", "carbono neutro", "energia solar", "energia eólica offshore",
    "internet das coisas", "iot", "smart devices", "smart home",
    "computação quântica", "qubit", "criptografia quântica", "teleporte quântico",
    "blockchain aplicações", "web3", "metaverso", "token", "crypto",
    "big data", "data science", "analytics", "privacidade de dados",
    "cibersegurança", "ransomware", "phishing", "zero trust", "mdm",
]

# Química: elementos e compostos
CHEM_ELEMENTS = [
    "hidrogênio", "hélio", "lítio", "berílio", "boro", "carbono", "nitrogênio",
    "oxigênio", "flúor", "néon", "sódio", "magnésio", "alumínio", "silício",
    "fósforo", "enxofre", "cloro", "argônio", "potássio", "cálcio",
    "escândio", "titânio", "vanádio", "cromo", "manganês", "ferro", "cobalto",
    "níquel", "cobre", "zinco", "gálio", "germânio", "arsênio", "selênio",
    "bromo", "criptônio", "rubídio", "estrôncio", "itrio", "zircônio",
    "nióbio", "molibdênio", "tecnécio", "rutênio", "ródio", "paládio",
    "prata", "cádmio", "índio", "estanho", "antimônio", "telurio", "iodo",
    "xenônio", "césio", "bário", "lantânio", "cério", "neodímio",
    "samário", "európio", "gadolínio", "térbio", "disprósio", "hólmio",
    "érbio", "túlio", "itérbio", "lutécio", "háfnio", "tântalo",
    "tungstênio", "rênio", "ósmio", "irídio", "platina", "ouro",
    "mercúrio", "tálio", "chumbo", "bismuto", "polônio", "astatina",
    "radônio", "frâncio", "rádio", "actínio", "tório", "protactínio",
    "urânio", "netúnio", "plutônio", "amerício", "curio", "berquélio",
    "califórnio", "einsténio", "férmio", "mendelévio", "nobélio",
    "laurencio", "elementos da tabela periódica", "tabela periódica completa",
    "molécula de água", "dióxido de carbono", "oxigênio molecular",
    "nitrogênio atmosférico", "ácido sulfúrico", "ácido clorídrico",
]

# Escritores e suas obras
WRITERS = [
    "machado de assis obras", "dom casmurro", "memórias póstumas de brás cubas",
    "quincas borba", "helena", "iaiá garcia", "esau e jacó",
    "carlos drummond poemas", "alguma poesia", "sentimento do mundo",
    "rosa do povo", "clarice lispector obras", "a hora da estrela",
    "laços de família", "paixão segundo g.h.", "guimarães rosa obras",
    "grande sertão veredas", "sagarana", "primeiras estórias",
    "jorge amado obras", "gabriela cravo e canela", "dona flor",
    "capitaês da areia", "tieta do agreste", "cacau",
    "josé lins do rego", "fogo morto", "menino de engenho",
    "graciliano ramos", "vidas secas", "são bernardo", "angústia",
    "machado de assis clássicos", "dom casmurro resumo", "vidas secas resumo",
    "grande sertão resumo", "casa grande e senzala", "gilberto freyre",
    "sergio buarque", "raízes do brasil", "caio prado junior",
    "formação do brasil", "história da literatura brasileira",
    "quincas borba resumo", "memórias póstumas resumo", "o cortiço",
    "aluísio azevedo", "o coração", "edar", "jorge michel", "amado arnoldo",
    "irmãos karamazov", "crime e castigo", "guerra e paz", "ana karenina",
    "cem anos de solidão", "cien años de soledad", "o verbo", "dom quixote",
    "laranja mecânica", "1984 george orwell", "revolução dos bichos",
    "o grande gatsby", "matadouro cinco", "cem anos de solidão resumo",
    "harry potter e a pedra filosofal", "jogos vorazes", "divergente",
]

# Séries brasileiras e novelas
SERIES_BR = [
    "a grande família", "tapas & beijos", "cidade de deus série", "3% série",
    "vida de otário", "segurança nacional", "ratas", "arremesso de ouro",
    "pré-candidato", "vai que cola", "clube da esquina", "dona de casa",
    "lendas do paraná", "série city of god", "irmandade", "os outros",
    "justiça", "o reverso da medalha", "vampiro de salvador",
    "novela roque santeiro", "vale a pena ver de novo", "a veneno",
    "novela a favorita", "senna série", "turma da monica laços",
    "novela do cafufa", "esse amor", "cheias de charme", "amor de mãe",
    "a força do querer", "segundo sol", "babilônia", "velho chico",
    "folha", "a dona do pedaço", "amor verdadeiro", "vidas em jogo",
    "cobras e lagartos", "caminho das índias", "a viagem", "roda da vida",
    "em família", "lado a lado", "espelho da vida", "a próxima vítima",
    "quatro por quatro", "sassaricando", "toperson", "o clone",
    "mulheres de areia", "tieta", "roque santeiro", "novela lua cheia",
    "senhora do destino", "a grande mentira", "o gerente do mundo",
]

# Termos de marketing e vendas
MARKETING_TERMS = [
    "marketing", "marketing digital", "marketing de conteúdo", "inbound marketing",
    "funil de vendas", "geração de leads", "lead", "conversão", "taxa de conversão",
    "landing page", "site de vendas", "e-commerce", "checkout", "carrinho",
    "branding", "identidade visual", "logo", "marca", "slogan", "jingle",
    "público-alvo", "persona", "segmentação", "niche", "mercado",
    "posicionamento", "proposta de valor", "diferencial", "benefício",
    "produto", "serviço", "preço", "custo", "margem", "lucro",
    "promoção", "desconto", "cupom", "frete grátis", "pix parcelado",
    "distribuição", "canais de venda", "omnichannel", "marketplace",
    "anúncio", "impulsionar", "patrocinado", "campanha", "criativo",
    "copy", "texto de venda", "CTA", "call to action", "título",
    "teste a/b", "otimização", "performance", "roi", "retorno sobre investimento",
    "cac", "custo de aquisição", "lifetime value", "ltv", "retenção",
    "brand awareness", "notoriedade", "engajamento", "alcance orgânico",
    "seo marketing", "tráfego", "tráfego pago", "tráfego orgânico", "tráfego direto",
    "social media", "influenciador", "micro influencer", "niche influencer",
]

# Economia e dinheiro (mais)
ECONOMY_TERMS = [
    "pib", "produto interno bruto", "inflação", "selic", "taxa de juros",
    "ipca", "índice de preços", "câmbio", "cotação dólar", "cotação euro",
    "bolsa de valores", "ibovespa", "aha", "b3", "índice da bolsa",
    "ações", "fiis", "tesouro direto", "cdb", "lci", "lca", "poupança",
    "renda fixa", "renda variável", "fundos de investimento", "etf",
    "criptomoedas", "bitcoin", "ethereum", "altcoin", "stablecoin",
    "blockchain", "mineração", "carteira digital", "wallet",
    "recessão", "recuperação econômica", "crescimento", "estagnação",
    "déficit", "superávit", "dívida pública", "teto de gastos", "arcabouço fiscal",
    "impostos", "iof", "icms", "iss", "inss", "fgts", "pis", "cofins",
    "declaração de imposto de renda", "imposto de renda 2026", "irpf",
    "restituição", "malha fina", "declarar rendimentos", "comprovante de renda",
    "pix", "transferência", "cédula", "moeda", "nota fiscal", "recibo",
    "orçamento", "planejamento financeiro", "meta financeira",
    "juros compostos", "regra dos 72", "valor do dinheiro no tempo",
    "aposentadoria", "pensão", "previdência privada", "vgb", "seguro de vida",
]

# Direito e leis (mais)
LAW_TERMS = [
    "direito trabalhista", "rescisão", "aviso prévio", "férias", "décimo terceiro",
    "salário mínimo", "piso salarial", "horas extras", "adicional noturno",
    "home office direito", "teletrabalho", "demissão sem justa causa",
    "demissão por justa causa", "estabilidade", "segurança do trabalho",
    "carteira de trabalho", "ctps", "sindicato", "negociação coletiva",
    "direito do consumidor", "código de defesa do consumidor", "direito de arrependimento",
    "garantia", "troca de produto", "reclamação", "procon", "litígio",
    "contrato", "cláusula", "rescisão contratual", "multa contratual",
    "direito civil", "casamento", "divórcio", "guarda de filhos", "pensão alimentícia",
    "herança", "testamento", "inventário", "adotar", "reconhecimento de paternidade",
    "direito penal", "pena", "prisão", "flagrante", "inquérito", "processo criminal",
    "advogado de defesa", "promotor de justiça", "juiz de direito", "tribunal",
    "recursos", "apelação", "sentença", "audiência", "depoimento",
    "direito constitucional", "direitos fundamentais", "liberdade de expressão",
    "direito de imagem", "direito autoral", "plágio", "propriedade intelectual",
    "registro de marca", "patente", "lei de proteção de dados", "lgpd",
    "marco civil da internet", "crime cibernético", "estelionato",
    "golpe", "fraude", "golpe do pix", "advocacia", "defensoria pública",
]

# Saúde e estilo de vida
HEALTH_LIFESTYLE = [
    "alimentação saudável", "dieta mediterrânea", "dieta vegana", "dieta vegetariana",
    "dieta low carb", "dieta cetogênica", "dieta paleo", "dieta flexível",
    "dieta para emagrecer", "dieta para ganhar massa", "dieta para hipertensos",
    "dieta para diabéticos", "intolerância à lactose", "intolerância ao glúten",
    "alergia alimentar", "alergia", "resposta imunológica", "imunidade",
    "suplementação", "vitamina c", "vitamina b12", "ferro", "cálcio",
    "magnésio", "omega 3", "creatina", "whey protein", "albumina",
    "proteína vegetal", "gordura boa", "gordura saturada", "transgênicos",
    "orgânico", "natural", "industrializado", "ultraprocessados",
    "exercício física", "cardio", "musculação para iniciantes", "treino de força",
    "treino aeróbico", "hipertrofia", "definição muscular", "alongamento",
    "aquecimento", "descanso", "recuperação muscular",
    "sono saudável", "dormir bem", "ciclo circadiano", "higiene do sono",
    "estresse crônico", "cortisol", "adrenalina", "relaxamento",
    "meditação", "respiração profunda", "yoga nidra", "pomodoro",
    "autoestima", "autoconfiança", "ansiedade social", "timidez",
    "workaholic", "burnout prevenção", "equilíbrio vida-trabalho",
    "gratidão", "mindset positivo", "resiliência", "motivação", "propósito",
]

# Mais animes e mangás
ANIME_MORE = [
    "naruto jogos", "naruto personagens", "sasuke", "sakura", "kakashi", "itachi",
    "naruto shippuden", "boruto", "jedai", "ohkrog", "sabre",
    "one piece personagens", "luffy", "zoro", "nami", "sanji", "chopper",
    "robin", "franky", "brook", "shanks", "ace", "sabo", "law",
    "dragon ball z", "goku", "vegeta", "gohan", "piccolo", "trunks",
    "cell", "freeza", "majin boo", "dragon ball super", "beerus",
    "attack on titan personagens", "eren", "mikasa", "armin", "levi",
    "demon slayer personagens", "tanjiro", "nezuko", "zenitsu", "inosuke",
    "my hero academia personagens", "deku", "bakugo", "ochaco", "all might",
    "jujutsu kaisen personagens", "yuji", "megumi", "nobara", "gojo",
    "sukuna", "chainsaw man personagens", "denji", "power", "aki", "makima",
    "one punch man", "saitama", "genos", "boku no hero", "shingeki",
    "frieren personagens", "fern", "starline", "slime", "tensura",
    "re zero", "konosuba", "overlord", "reincarnated", "isekai",
    "sword art online", "kirito", "asuna", "fairy tail", "natsu",
    "black clover", "asta", "yuno", "fire force", "shinra",
    "bluelock", "kuroko no basket", "haikyuu", "hinata", "kageyama",
    "inazuma eleven", "pokémon anime", "digimon anime", "yu-gi-oh",
    "spy x family personagens", "day", "anya", "yor", "loid",
    "kimi no na wa", "spirited away resumo", "howl resumo", "totoro resumo",
]

# Mais filmes e séries
MOVIES_MORE = [
    "avatar resumo", "titanic resumo", "interestelar resumo", "matrix resumo",
    "senhor dos anéis resumo", "harry potter resumo", "star wars resumo",
    "vingadores resumo", "jurassic park resumo", "de volta para o futuro resumo",
    "o poderoso chefão resumo", "pulp fiction resumo", "clube da luta resumo",
    "angry", "gladiador resumo", "forrest gump resumo", "green mile resumo",
    "cidade de deus resumo", "tropa de elite resumo", "auto da compadecida resumo",
    "central do brasil resumo", "a esperança", "interestelar resumo",
    "inception final", "matrix final", "se7en", "memento", "prestige",
    "duna", "duna parte dois", "blade runner", "2001 uma odisseia",
    "la la land", "whiplash", "the pianist", "schindler's list",
    "12 anos de escravidão", "the social network", "frankstein", "dracula",
    "sherlock holmes filmes", "james bond", "o agente secreto",
    "mission impossible", "john wick", "the matrix resumo", "a bela e a fera",
    "a pequena sereia", "aladdin", "moana", "encanto resumo", "coco resumo",
    "soul pixar", "divertidamente resumo", "up altas aventuras", "wall-e",
    "ratatouille", "monsters inc", "cars", "toy story", "shrek resumo",
    "madagascar", "how to train your dragon", "kung fu panda resumo",
    "the dark knight", "batman begins", "o cavaleiro das trevas",
    "spider-man filmes", "homem-aranha longe de casa", "adam project",
    "tenet", "interstellar", "gravity", "the martian", "arrival",
    "blade runner 2049", "duna 2021", "everything everywhere",
    "parasite", "the whale", "belfast", "roma filme",
]

# Mais músicas e artistas (álbuns)
MUSIC_ALBUMS = [
    "thriller michael jackson", "bad", "dangerous", "off the wall",
    "abbey road", "let it be", "sgt. pepper's", "revolver", "the white album",
    "dark side of the moon", "the wall", "wish you were here",
    "nevermind nirvana", "in utero", "bleach",
    "master of puppets", "metallica black", "ride the lightning",
    "back in black", "highway to hell", "the number of the beast",
    "a night at the opera", "news of the world", "kind of magic",
    "born this way", "the fame", "reputation", "1989 taylor swift",
    "folklore", "evermore", "midnights",
    "lemonade", "dangerously in love", "renaissance",
    "after hours", "blinding lights", "starboy",
    "ukulele", "sian", "anitta albums", "funk generation",
    "sertanejo raiz albuns", "marília mendonça álbuns", "gusttavo lima álbuns",
    "jorge e mateus álbuns", "ze neto álbuns", "henrique e juliano álbuns",
    "legião urbana álbuns", "dois", "que país é este", "as quatro estações",
    "raimundos álbuns", "skank álbuns", "paralamas álbuns", "titas álbuns",
    "charlie brown jr álbuns", "capital inicial álbuns", "os paralamas álbuns",
    "titãs álbuns", "engenheiros do hawaii álbuns", "ultraje a rigor",
    "pitty álbuns", "angra álbuns", "sepultura álbuns", "clone",
]

# Mais artistas brasileiros
ARTISTS_BR = [
    "anitta", "ivvy", "ludmilla", "alok", "mc rabelo", "mc ig", "mc kevin",
    "mc livinho", "mc pedrinho", "mc guimê", "mc sofrência", "mc don Juan",
    "mc harry", "mc deluxe", "mc du boa", "mc marcinho",
    "gusttavo lima", "jorge e mateus", "marília mendonça", "ze neto e cristiano",
    "henrique e juliano", "bruno e marrone", "daniel e samuel", "leo santana",
    "simone mendes", "maraisa", "maiara", "wellinton", "dilsinho",
    "luan santana", "cristiano araújo", "chitãozinho e xororó",
    "beto carrero", "belchior", "dias de oliveira", "elomar",
    "caetano veloso", "gilberto gil", "gal costa", "maria bethânia",
    "ivete sangalo", "claudia leitte", "margareth menezes", "olodum",
    "trio eletrico", "baiana system", "axé 90", "dança do passinho",
    "mc fantasy", "mc luccas", "mc veiga", "mc duguinho", "mc da geração",
    "pabllo vittar", "gêmeas", "glória groove", "liniker", "djavan",
    "seu jorge", "milton nascimento", "orquestra", "grupo baiana",
    "baiana reclaim", "mc danone", "mc bin", "mc kaio", "mc teteu",
    "nattan", "felipe amorim", "yuri redicopa", "mc donca", "nickson reis",
]

# Idiomas do mundo
LANGUAGES = [
    "português", "inglês", "espanhol", "francês", "alemão", "italiano", "russo",
    "mandarim", "chinês", "japonês", "coreano", "árabe", "hindi", "bengali",
    "turco", "persa", "urdu", "indonésio", "malaio", "tailandês", "vietnamita",
    "flamengo", "holandês", "sueco", "norueguês", "dinamarquês", "finlandês",
    "islandês", "polonês", "tcheco", "eslovaco", "húngaro", "romeno", "búlgaro",
    "sérvio", "croata", "grego", "hebraico", "amárico", "suaili", "iarubá",
    "zulu", "africâner", "tupi", "guarani", "nheengatu", "língua de sinais",
    "braille", "libras", "esperanto", "latim", "grego antigo", "sânscrito",
    "arameu", "hieróglifos", "cuneiforme", "escrita cuneiforme", "kana",
    "kanji", "hiragana", "katakana", "alfabeto cirílico", "alfabeto árabe",
    "alfabeto grego", "alfabeto hebraico", "alfabeto devanágari",
    "língua mais falada", "língua oficial do brasil", "idioma mais falado do mundo",
    "espanhol na américa", "português no mundo", "inglês como língua global",
]

# Religiões do mundo (mais)
RELIGIONS_WORLD = [
    "hinduísmo", "budismo", "jainismo", "siquismo", "confucionismo", "taoísmo",
    "xintoísmo", "zoroastrismo", "judaísmo", "cristianismo", "islamismo",
    "bahai", "espiritualismo", "espiritismo kardecista", "umbanda", "candomblé",
    "santeria", "vodun", "igreja católica", "ortodoxa", "protestantismo",
    "pentecostal", "evangélico", "mórmon", "testemunhas de jeová", "adventista",
    "batista", "metodista", "luterana", "presbiteriana", "anglicana",
    "calvinismo", "ariano", "sufismo", "xiismo", "sunismo", "wahabismo",
    "jainismo", "sikhismo", "zen", "vipassana", "meditação transcendental",
    "igreja da scientologia", "religiões afro-brasileiras", "candomblé origem",
    "umbanda origem", "religiosidade popular", "paganismo", "wicca",
    "xamanismo", "animismo", "totemismo", "politeísmo", "monoteísmo",
    "ateísmo", "agnosticismo", "deísmo", "panteísmo", "espiritualidade",
]

# Povos e étnicos
PEOPLES = [
    "povos indígenas do brasil", "tupi", "guarani", "aiuru", "pataxó", "apinajé",
    "kayapó", "mundo", "terena", "kaingang", "xavante", "bororo", "kuikuro",
    "yanomami", "ye'kwana", "macuxi", "wai-wai", "cinta-larga", "kadiwéu",
    "enawene-nawe", "suruwahá", "zuruahã", "pirahã", "desana", "tucano",
    "caribes", "arawak", "tupi-guarani", "je", "bororo", "carajá",
    "nativos americanos", "navajo", "cherokee", "sioux", "apaches", "comanches",
    "incas", "aiacuchu", "quechua", "aimará", "mapuche", "maya", "asteca",
    "aztécas", "olmecas", "totonacas", "zapotecas", "mixtecas", "purepechas",
    "aborígenes australianos", "maori", "sami", "inuit", "esquimó", "abkhaz",
    "curdos", "basco", "catalão", "galego", "bretão", "córsega",
    "cigano", "romani", "judu", "tibetanos", "uygures", "pathan",
]

# Arquitetura e monumentos
ARCHITECTURE = [
    "arquitetura", "arquitetura moderna", "arquitetura clássica", "arquitetura gótica",
    "arquitetura barroca", "arquitetura românica", "arquitetura renascentista",
    "arquitetura contemporânea", "arquitetura sustentável", "bioclimática",
    "museu", "igreja gótica", "catedral", "catedral de notre dame",
    "sagrada família", "coliseu de roma", "partenon", "templo de karnak",
    "machu picchu", "chichén itzá", "petra", "coliseu", "torre de pizza",
    "torre eiffel", "big ben", "estátua da liberdade", "cristo redentor",
    "torre de toquio", "burj khalifa", "torre de londres", "abas door",
    "palácio de versalhes", "palácio de buckingham", "kremlin", "castelo de neuschwanstein",
    "castelo de windsor", "alcázar", "muralha da china", "grande muralha",
    "taj mahal", "petra ruínas", "angkor wat", "borobudur", "pont du gard",
    "panteão", "basílica de são pedro", "mosteiro", "convento", "mosteiro de são bento",
    "obra social", "skyscraper", "arranha-céu", "ponte", "viaduto", "túnel",
    "faro", "lighthouse", "estádio", "arena", "aeroporto arquitetura",
    "urbanismo", "cidades inteligentes", "planejamento urbano", "mobilidade urbana",
]

# Ecologia e meio ambiente
ECOLOGY = [
    "ecologia", "ecossistema", "biodiversidade", "bioma", "habitat", "nicho ecológico",
    "cadeia alimentar", "teia alimentar", "produtores", "consumidores", "decompositores",
    "reciclagem", "reduzir reutilizar reciclar", "compostagem", "lixo", "resíduos",
    "lixo eletrônico", "lixo plástico", "poluição plástica", "petróleo no mar",
    "água potável", "crise hídrica", "secas", "desertificação", "perda de biodiversidade",
    "espécies ameaçadas", "extinção", "animais em extinção", "onça em extinção",
    "conservação", "unidade de conservação", "parques nacionais", "reserva ambiental",
    "reflorestamento", "desmatamento", "queimadas", "incêndios florestais",
    "mudanças climáticas", "aquecimento global", "qceo", "efeito estufa",
    "energia renovável", "energia solar", "energia eólica", "energia hidrelétrica",
    "energia geotérmica", "energia de biomassa", "biogás", "hidrogênio",
    "pegada de carbono", "carbono neutro", "crédito de carbono", "net zero",
    "sustentabilidade", "agricultura sustentável", "agroecologia", "agricultura orgânica",
    "permacultura", "proteção animal", "direitos dos animais", "veganismo",
    "reciclagem de lixo", "coleta seletiva", "economia circular",
]

# Psicologia
PSYCHOLOGY = [
    "psicologia", "psicologia clínica", "psicologia social", "psicologia comportamental",
    "behaviorismo", "cognitivismo", "psicanálise", "psicologia da personalidade",
    "inteligência", "q I", "q2", "quociente emocional", "eq",
    "memória", "memória de curto prazo", "memória de longo prazo", "esquecimento",
    "aprendizagem", "condicionamento", "pavlov", "operant", "reforço", "punição",
    "motivação", "emoção", "sentimentos", "estado de humor", "estresse",
    "ansiedade", "fobia", "transtorno", "depressão", "bipolaridade",
    "transtorno de personalidade", "narcisismo", "borderline", "esquizofrenia",
    "autismo", "tdah", "dislexia", "discalculia",
    "psicologia infantil", "psicologia do desenvolvimento", "desenvolvimento infantil",
    "fases do desenvolvimento", "adolescência", "maturidade", "envelhecimento",
    "psicologia organizacional", "liderança", "trabalho em equipe", "conflito",
    "persuasão", "influência", "conformidade", "obediência", "igualmas",
    "subconsciente", "inconsciente", "sonhos significado", "projeção psicológica",
    "introversão", "extroversão", "personalidade segundo jung", "16 tipos",
    "en comum", "testes psicológicos", "avaliação psicológica", "psicodiagnóstico",
]

# Sociologia
SOCIOLOGY = [
    "sociologia", "sociedade", "classes sociais", "estratificação", "mobilidade social",
    "cultura", "subcultura", "contracultura", "normas sociais", "valores",
    "instituições sociais", "família sociologia", "religião sociologia", "educação sociologia",
    "economia sociologia", "política sociologia", "trabalho sociologia",
    "desigualdade", "pobreza", "exclusão social", "preconceito", "discriminação",
    "racismo", "machismo", "homofobia", "eldade", "intolerância religiosa",
    "direitos civis", "movimentos sociais", "movimento feminista", "movimento negro",
    "movimento lgbt", "movimento estudantil", "movimento operário", "sindicato",
    "globalização", "capitalismo", "socialismo", "comunismo", "liberalismo",
    "neoliberalismo", "populismo", "autoritarismo", "democracia", "república",
    "monarquia", "ditadura", "totalitarismo", "fascismo", "nazismo",
    "sociologia de durkheim", "anomia", "fato social", "marxismo", "luta de classes",
    "modo de produção", "mais-valia", "alienação", "ideologia", "hegemonia",
    "cultura de massa", "indústria cultural", "escola de frankfurt", "consumo",
    "sociedade de consumo", "sociedade do espetáculo", "biopoder", "disciplina",
]

# História mundial (mais)
WORLD_HISTORY = [
    "pré-história", "idade da pedra", "idade do bronze", "idade do ferro",
    "antiguidade", "idade média", "renascimento", "era dos descobrimentos",
    "revolução industrial", "revolução francesa", "era napoleônica", "unificação alemã",
    "unificação italiana", "imperialismo", "colonialismo", "primeira guerra mundial",
    "segunda guerra mundial", "guerra fria", "cortina de ferro", "muro de berlim",
    "queda da união soviética", "revolução russa", "revolução chinesa", "maoismo",
    "guerra da coreia", "guerra do vietnã", "guerra civil espanhola", "guerra civil americana",
    "guerras púnicas", "guerras médicas", "conquista da américa", "colonização da américa",
    "escravidão atlântica", "tráfico negreiro", "abolicionismo", "independência das américas",
    "revolução haitiana", "revolução mexicana", "revolução cubana", "cuban missile crisis",
    "crise dos mísseis", "guerra do vietnã história", "boom coffee", "chimon",
    "idade média feudalismo", "feudalismo", "servo", "senhor feudal", "castelo feudal",
    "cidades medievais", "peste negra", "cruzadas", "peste bubônica",
    "império bizantino", "império romano", "império inca", "império maia", "império asteca",
    "império otomano", "império mongol", "gengis khan", "safavids", "seljúcidas",
    "renascimento italiano", "flo", "medici", "borgia", "galileu e a igreja",
]

# Segurança e defesa
SECURITY = [
    "segurança", "segurança pública", "violência", "criminalidade", "crimes",
    "policiamento", "investigação criminal", "perícia", "identificação", "impressão digital",
    "defesa", "exército", "marinha", "força aérea", "polícia", "polícia militar",
    "polícia civil", "polícia federal", "guardas", "exército brasileiro",
    "cibersegurança", "hacker", "criptografia", "senha", "autenticação",
    "biometria", "reconhecimento facial", "monitoramento", "câmera de segurança",
    "alarme residencial", "fechadura", "cofre", "trancar", "cadeado",
    "primeiros socorros", "emergência", "samu", "bombeiros", "heliporto",
    "evacuação", "plano de emergência", "extintor", "incêndio", "prevenção de incêndio",
    "segurança do trabalho", "epi", "equipamento de proteção", "nr", "norma regulamentadora",
    "seguro", "seguro residencial", "seguro automóvel", "seguro de vida",
    "vigia", "escolta", "segurança pessoal", "proteção de dados", "lgpd",
]

# Família e relações
FAMILY_REL = [
    "família", "casamento", "namoro", "noivado", "união estável", "divórcio",
    "separação", "guarda compartilhada", "família monoparental", "família homoafetiva",
    "paternidade", "maternidade", "adolescência", "crise de identidade",
    "relacionamento", "ciúmes", "confiança", "comunicação no relacionamento",
    "reconciliação", "término", "redescoberta", "conflito familiar", "briga de irmãos",
    "educar filhos", "limites para filhos", "disciplina positiva", "punição",
    "rotina familiar", "alimentação da família", "reunião de família", "tradição",
    "olid", "avós", "netos", "primos", "tios", "padrinhos", "madrinha",
    "amizade", "fazer amigos", "amigo verdadeiro", "socialmente", "timidez",
    "solidão", "introversão", "círculo social", "comunidade", "vizinhança",
    "rede de apoio", "acolhimento", "empatia", "compaixão", "ajuda mútua",
    "relação à distância", "namoro à distância", "longa distância", "reencontro",
]

# Comunicação
COMMUNICATION = [
    "comunicação", "comunicação verbal", "comunicação não-verbal", "linguagem corporal",
    "escuta ativa", "feedeback", "conversa", "diálogo", "debate", "discussão",
    "argumentação", "persuasão", "negociação", "oratória", "falar em público",
    "apresentar", "slide", "storytelling", "narrativa", "narrar",
    "telefone", "ligação", "videoconferência", "reunião online", "webinar",
    "email", "mensagem", "chat", "áudio", "nota de voz", "papel",
    "cartaz", "pôster", "flyer", "folder", "panfleto", "anúncio",
    "comunicado", "aviso", "nota oficial", "release", "press release",
    "jornal", "revista", "tv", "rádio", "podcast", "mídia", "veículo",
    "repórter", "entrevista", "cobertura", "notícia", "matéria", "colunista",
    "rede social profissional", "comunicação interna", "comunicação externa",
]

# Geopolítica e relações internacionais
GEO_POLITICS = [
    "geopolítica", "guerra", "conflito", "sanção", "embargo", "paz",
    "diplomacia", "acordo internacional", "tratado", "aliança", "bloco econômico",
    "nação", "estado", "soberania", "fronteira", "território", "colonização",
    "globalização", "hegemonia", "potência", "superpotência", "país emergente",
    "paises em desenvolvimento", "país desenvolvido", "país subdesenvolvido",
    "descolonização", "colonização da áfrica", "partilha da áfrica", "conferência de berlim",
    "conflito israel-palestina", "palestina", "fiança", "faixa de gaza", "crise do oriente médio",
    "guerra da ucrânia 2026", "invasão da ucrânia", "rússia-ucrânia conflito",
    "crise na venezuela", "crise na síria", "conflito no iêmen", "conflito no sudão",
    "guerra comercial china-usa", "rivalidade china-eua", "roteiro da américa",
    "vízios", "otan expansão", "nato leste", "mercado comum do sul", "mercosul",
    "união européia", "ue evolução", "brexit", "moeda única europeia", "eurozona",
    "países brics", "brics 2026", "g20 2026", "g7 2026", "cop26", "cop27", "cop28",
    "onu conselho de segurança", "us veto", "placas", "nuclear", "arma nuclear",
    "desarmamento", "tratado de não proliferação nuclear", "energia nuclear militar",
]

# Agricultura e alimentos
AGRI_FOOD = [
    "agricultura", "agronegócio", "agropecuária", "plantio", "colheita", "safra",
    "semente", "mudas", "solo", "adubo", "fertilizante", "agrotóxico",
    "pragas agrícolas", "pragas da lavoura", "pesticida", "herbicida", "fungicida",
    "irrigação", "gotejamento", "trator", "colheitadeira", "arado", "plantadeira",
    "rotação de culturas", "reforma agrária", "posse da terra", "latifúndio", "minifúndio",
    "produção agrícola", "exportação agrícola", "commodities", "soja", "milho", "trigo",
    "café", "cana-de-açúcar", "algodão", "arroz", "feijão", "banana", "laranja",
    "pectin", "manejo", "pasto", "gado", "bovinocultura", "suinocultura", "avicultura",
    "leite", "ordenha", "queijo artesanal", "apicultura", "mel", "pesca",
    "aquicultura", "piscicultura", "criação de peixes", "carcinicultura",
    "agricultura familiar", "horta comunitária", "pente", "fumaça", "terra",
    "segurança alimentar", "fome", "desnutrição", "alimentação escolar", "pnae",
]

# Educação infantil e crianças
CHILDREN_EDU = [
    "educação infantil", "creche", "pré-escola", "kindergarten", "maternal",
    "berçário", "desfralde", "alfabetização", "lição de casa", "dever de casa",
    "tarefa escolar", "reforço escolar", "material escolar", "mochila escolar",
    "uniforme", "merenda escolar", "lancheira", "intervalo", "recreio",
    "brincar", "brincadeira", "jogos educativos", "quebra-cabeça", "lego",
    "dia da criança", "brinquedos", "boneca", "carrinho", "batedor", "bola",
    "desenho infantil", "colorir", "pintura", "plasticina", "massinha",
    "contos de fadas", "fábula", "história infantil", "cantigas", "parlendas",
    "trava-língua", "rimas", "música infantil", "dança infantil",
    "creche pública", "educação infantil pública", "ensino fundamental", "ensino médio",
    "escola particular", "escola pública", "escola bilíngue", "portal da transparência",
    "reprovação", "evasão escolar", "bullying", "cyberbullying", "inclusão escolar",
    "educação especial", "professor de apoio", "reforço", "tutoria", "mentoria",
]

# Idosos e envelhecimento
ELDERLY = [
    "terceira idade", "idosos", "envelhecimento", "geriatria", "gerontologia",
    "velhice", "longevidade", "qualidade de vida na terceira idade",
    "aposentadoria", "benefício", "bpc", "inss", "pensão", "consignado",
    "saúde do idoso", "osteoporose", "catarata", "artrite", "demência", "alzheimer",
    "mobilidade", "queda em idosos", "equilíbrio", "fisioterapia", "reabilitação",
    "cuidador", "cuidador de idosos", "asilo", "casa de repouso", "instituição de longa permanência",
    "convivência", "solidão", "acompanhamento", "visita", "família do idoso",
    "autonomia", "independência", "documentos do idoso", "estatuto do idoso",
    "direitos dos idosos", "proteção ao idoso", "violência contra o idoso",
    "envelhecimento ativo", "atividade física na terceira idade", "hidroginástica",
    "alimentação do idoso", "suplementação para idosos", "calcio", "vitamina b12",
    "memória do idoso", "jogos de memória", "lazer para idosos", "grupo da terceira idade",
    "pensão por morte", "benefício de prestação continuada", "inatividade",
]

# Transporte e mobilidade (mais)
TRANSPORT_MORE = [
    "mobilidade urbana", "trânsito", "congestionamento", "engenharia de tráfego",
    "sinalização", "semáforo", "faixa de pedestre", "faixa exclusiva", "ciclovia",
    "ciclorrota", "transporte público", "ônibus", "metrô", "trem", "vlt",
    "bilhete único", "cartão de transporte", "recarga", "integração",
    "aplicativo de transporte", "uber", "99", "cabify", "blablacar", "carona",
    "carro por assinatura", "aluguel de carro", "car shing", "moto por assinatura",
    "estacionamento", "parking", "zona azul", "garagem", "drive",
    "pedágio", "toll", "motorista profissional", "cnh", "habilitação", "exame de direção",
    "autoescola", "aula de direção", "primeira habilitação", "renovação da cnh",
    "multas de trânsito", "infração", "pontos na carteira", "suspensão da cnh",
    "direção defensiva", "seguro de trânsito", "acidente de trânsito",
    "resgate", "guincho", "reboque", "oficina mecânica", "revisão do carro",
    "manutenção", "troca de óleo", "pneu", "balanceamento", "alinhamento",
]

# Meteorologia avançada
WEATHER_ADV = [
    "meteorologia", "climatologia", "previsão do tempo", "tempo amanhã",
    "clima de são paulo", "clima do rio de janeiro", "clima do nordeste",
    "clima do sul do brasil", "clima do sudeste", "clima do centro-oeste",
    "fenômenos meteorológicos", "frente fria", "frente quente", "massa de ar",
    "massa polar", "massa de ar quente", "alta pressão", "baixa pressão",
    "zona de convergência", "cavado", "crista", "vórtice ciclônico",
    "jet stream", "correntes de jato", "el niño", "la niña", "enso",
    "monção", "chuvas de verão", "chuvas de inverno", "chuvas ácidas",
    "granizo", "neve", "geada", "neblina", "nevoeiro", "vento forte",
    "tempestade tropical", "ciclon", "furacão", "tornado", "vendaval",
    "ciclone extratropical", "onda de calor", "onda de frio", "seca prolongada",
    "enchente", "transbordamento", "encosta", "deslizamento de terra",
    "alerta meteorológico", "radar meteorológico", "imagens de satélite",
    "índice de qualidade do ar", "poluição do ar", "material particulado",
]

# Ciência de dados e tecnologia
DATA_SCI = [
    "ciência de dados", "análise de dados", "estatística", "probabilidade",
    "big data", "banco de dados", "sql", "python", "r", "spss", "stata",
    "excel avançado", "planilha", "tabela dinâmica", "gráficos", "dashboard",
    "machine learning", "aprendizado supervisionado", "aprendizado não supervisionado",
    "regressão", "classificação", "clusterização", "árvore de decisão",
    "rede neural", "deep learning", "processamento de linguagem", "nlp",
    "visão computacional", "reconhecimento de imagem", "reconhecimento de fala",
    "inteligência artificial", "ia generativa", "chatbot", "assistente virtual",
    "automação", "robótica", "internet das coisas", "iot", "nuvem", "cloud",
    "segurança da informação", "criptografia", "blockchain", "web3",
    "desenvolvimento de software", "programação", "testes", "qualidade de software",
    "devops", "ci", "cd", "conteiner", "docker", "kubernetes",
    "banco de dados no sql", "mongodb", "cassandra", "elasticsearch",
    "data lake", "data warehouse", "etl", "pipelines de dados",
]

# Trading e investimentos
TRADING = [
    "investir", "onde investir", "como investir", "primeiros investimentos",
    "renda fixa", "tesouro direto", "cdb", "lci", "lca", "fundos",
    "ações", "fii", "etf", "criptomoedas", "bitcoin", "day trade",
    "trade", "swing trade", "longo prazo", "curto prazo", "reservar",
    "dividendos", "juros", "composto", "inflação", "risco", "retorno",
    "diversificação", "carteira", "alocação", "perfil de investidor",
    "conservador", "moderado", "arrojado", "renda variável", "setor de tecnologia",
    "ações de banco", "ações de petróleo", "índice", "ibovespa", "s&p 500",
    "dólar", "euro", "câmbio", "imóveis", "fundos imobiliários",
    "aposentadoria", "previdente", "previdência privada", "vgb",
    "análise fundamentalista", "análise técnica", "indicadores", "balanço",
    "demonstrativo de resultado", "lucro", "prejuízo", "receita", "capital",
    "alavancagem", "stop loss", "take profit", "gestão de risco",
]

# Artesanato e DIY (mais)
HANDCRAFT = [
    "artesanato", "diy", "faça você mesmo", "upcycling", "reaproveitamento",
    "reciclagem criativa", "decoração diy", "marcenaria", "carpintaria",
    "serralheria", "solda", "costura", "bordado", "crochê", "tricô",
    "tecelagem", "rendeirás", "ponto cruz", "macramê", "biscuit",
    "pintura", "aquarela", "acrílica", "guache", "mosaico", "vitral",
    "cerâmica", "argila", "barlo", "resina", "epóxi", "silicone",
    "papelaria criativa", "scrapbook", "cartonagem", "pasta americana",
    "bolo decorado", "confeitaria artística", "chocolates artesanais",
    "velas artesanais", "sabonetes artesanais", "perfumaria artesanal",
    "jardinagem diy", "vasos decorados", "palete", "madeira de demolição",
    "iluminação diy", "luminária", "arranjo de flores", "kokedama",
    "bonecos de feltro", "amigurumi", "pano de prato", "kit helado",
]

# Festivais e eventos
FESTIVALS = [
    "carnaval", "festival", "festa", "show", "concerto", "musical",
    "festival de música", "festival de cinema", "festival de gastronomia",
    "festival de dança", "festival junino", "festa junina", "festa do peão",
    "rodeio", "vaquejada", "festival de inverno", "reveillon", "virada",
    "réveillon na praia", "ano novo", "natal", "páscoa", "boom",
    "festa do padroeiro", "festa de aniversário", "casamento", "batizado",
    "churrasco com amigos", "confraternização", "happy hour", "evento corporativo",
    "feira", "exposição", "mostra", "salão", "congresso", "simpósio",
    "workshop", "oficina", "seminário", "palestra", "conferência",
    "festa literária", "flica", "bienal do livro", "flip", "bienal de arte",
    "expo", "olimpíadas", "competição", "campeonato", "prêmio", "festa popular",
    "festa de são joão", "festa do caju", "festa do açaí", "festa da uva",
]

# Farmácia e medicamentos
PHARMACY = [
    "paracetamol", "dipirona", "ibuprofeno", "nimesulida", "omeprazol",
    "amoxicilina", "azitromicina", "loratadina", "cetirizina", "dipirona monoidratada",
    "maleato de dexclorfeniramina", "diclov", "voltaren", "dexametasona",
    "prednisona", "ibuprofeno infantil", "xarope", "gripal", "soro fisiológico",
    "soro caseiro", "colírio", "pomada", "creme", "gel", "spray", "pastilha",
    "suplemento", "vitamina d3", "vitamina c", "omega 3", "cálcio", "ferro",
    "zinco", "magnésio", "probiótico", "colágeno", "creatina", "whey",
    "pré-natal", "ferro grávida", "ácido fólico", "metformina", "insulina",
    "losartana", "enalapril", "hidroclorotiazida", "simvastatina", "rosuvastatina",
    "levotiroxina", "anticoncepcional", "pílula", "adipeína", "sirt",
    "remédio para dor de cabeça", "remédio para febre", "remédio para tosse",
    "remédio para gripe", "remédio para enjoo", "remédio de estômago",
    "antibiótico natural", "analgésico natural", "fitoterápico", "plantas medicinais",
    "chá de camomila", "chá de hortelã", "chá de erva-doce", "chá de gengibre",
    "interação medicamentosa", "horário de tomar remédio", "bula", "receita médica",
    "dose", "sobredose", "efeito colateral", "reação alérgica", "descarte de remédio",
    "farmácia popular", "programa de medicamentos", "tarja preta", "tarja vermelha",
]

# Turismo (mais)
TOURISM_MORE = [
    "ecoturismo", "turismo de aventura", "turismo religioso", "turismo gastronômico",
    "turismo cultural", "turismo de negócios", "turismo de lazer", "turismo rural",
    "turismo sustentável", "turismo espacial", "turismo de bem-estar", "spa",
    "hotel", "resort", "pousada", "hostel", "airbnb", "aluguel por temporada",
    "reserva", "check-in", "check-out", "café da manhã", "pensão completa",
    "meia pensão", "all inclusive", "pacote turístico", "passagem aérea",
    "milhas", "pontos", "fidelidade", "counter", "bagagem", "malas",
    "check-in online", "raio-x aeroporto", "controle de passaporte", "imigração",
    "alfândega", "aduana", "taxa de embarque", "tripulação", "piloto",
    "guia turístico", "grupo de viagem", "selfie turística", "ponto turístico",
    "roteiro de viagem", "itinerário", "mapa da cidade", "guia da cidade",
    "idioma no exterior", "tradução de viagem", "moeda estrangeira", "câmbio",
    "seguro viagem", "seguro saúde internacional", "emergência no exterior",
    "consulado brasileiro", "visto de turismo", "visto de trabalho", "green card",
    "feriado emenda", "ponte", "feriado prolongado", "data ideal para viajar",
    "destino barato", "destino de inverno", "destino de verão", "praia paradisíaca",
]

# Livros e leitura (mais)
BOOKS_MORE = [
    "best-seller", "lançamento de livro", "livro de ficção", "livro de não-ficção",
    "romance", "suspense", "terror", "fantasia", "ficção científica", "aventura",
    "policial", "thriller", "distopia", "autobiografia", "biografia livro",
    "memórias", "ensaio", "crônica", "poesia livro", "contos", "novela",
    "quadrinhos livro", "graphic novel", "mangá livro", "light novel",
    "clássico da literatura", "clássicos infantis", "literatura brasileira",
    "literatura portuguesa", "literatura mundial", "literatura latino-americana",
    "literatura africana", "literatura de cordel", "poesia de cordel",
    "livro de autoajuda", "livro de desenvolvimento pessoal", "livro de finanças",
    "livro de negócios", "livro de história", "livro de ciência", "livro infantil",
    "livro de colorir", "livro de atividades", "livro de receitas",
    "ebook", "audiolivro", "livro digital", "kindle", "leitor de ebook",
    "biblioteca pública", "livraria", "sebo", "feira do livro", "lançamento",
    "preço de livro", "melhores livros", "livros para ler 2026", "marcar livro",
    "ficha de leitura", "resenha de livro", "clube de leitura", "desafio de leitura",
]

# Streaming e entretenimento (mais)
STREAMING = [
    "netflix", "disney plus", "hbo max", "prime video", "paramount plus",
    "star plus", "globoplay", "apple tv", "crunchyroll", "funimation",
    "deezer", "apple music", "spotify", "youtube music", "amazon music",
    "tidal", "soundcloud", "mixcloud", "bandcamp",
    "twitch", "kick", "youtube live", "facebook live", "instagram live",
    "podcast", "videocast", "streaming de jogos", "cloud gaming", "geforce now",
    "stremio", "plex", "kodi", "emby", "jellyfin",
    "assinatura", "plano", "premium", "gratuito", "teste grátis",
    "qualidade de streaming", "hd", "4k", "8k", "dolby",
    "olhar", "film", "catálogo", "novidades", "lançamentos",
    "netflix preço", "spotify preço", "como assinar", "cancelar assinatura",
    "familia", "perfil infantil", "controles parentais", "modo offline", "download",
    "legenda", "dublagem", "idioma", "áudio original",
    "melhores séries streaming", "melhores filmes streaming", "top 2026",
]

# Política brasileira
BR_POLITICS = [
    "presidente do brasil", "governador", "prefeito", "senador", "deputado federal",
    "deputado estadual", "vereador", "ministro", "supremo tribunal", "stf",
    "congresso nacional", "câmara dos deputados", "senado federal",
    "eleições", "voto", "urna eletrônica", "justiça eleitoral", "te",
    "partidos políticos", "psdb", "pt", "psl", "pl", "novo", "pode", "mdb",
    "aliança", "coligação", "coalização", "frente", "oposição", "base aliada",
    "governo federal", "governo estadual", "governo municipal", "separação de poderes",
    "executivo", "legislativo", "judiciário", "poder constituinte", "reforma política",
    "reforma eleitoral", "macrozona", "impeachment", "pedido de impeachment",
    "crise política", "corrupção", "lava jato", "operação", "investigação",
    "orçamento público", "lei orçamentária", "lc", "ploa", "loa", "auditoria",
    "transparência pública", "portal da transparência", "dados abertos", "lgpd público",
    "política externa", "relações internacionais", "embaixada", "diplomacia",
    "política econômica", "reforma tributária", "reforma previdenciária", "reforma trabalhista",
    "política de saúde", "sus", "política de educação", "política ambiental",
    "política de segurança", "política social", "bolsa família", "auxílio",
]

# Energia
ENERGY = [
    "energia elétrica", "geração de energia", "usina", "hidrelétrica", "termelétrica",
    "nuclear", "eólica", "solar", "biomassa", "geotérmica", "maremotriz",
    "usina hidrelétrica de itaipu", "usina nuclear angra", "turbina", "gerador",
    "transformador", "subestação", "linha de transmissão", "rede elétrica",
    "distribuição de energia", "conta de luz", "bandeira tarifária", "tarifa",
    "custo de energia", "tarifa social", "energia mais barata", "economia de energia",
    "poupar energia", "consumo de energia", "medidor", "kwh", "watts", "voltagem",
    "bateria", "carregador", "pilha", "recarregável", "célula de combustível",
    "energia renovável no brasil", "matriz energética", "matriz elétrica",
    "geração distribuída", "energia solar residencial", "painel solar", "placa solar",
    "microgeração", "bateria doméstica", "armazenamento de energia",
    "eficiência energética", "selo procel", "economizador", "lâmpada led",
    "apagão", "blackout", "corte de energia", "reestabelecimento", "manutenção elétrica",
]

# Moda (mais)
FASHION_MORE = [
    "moda", "tendência", "estilo", "look", "outfit", "production",
    "vestido", "saia", "blusa", "camisa", "calça", "shorts", "jaqueta",
    "casaco", "blazer", "moletom", "camiseta", "polo", "regata", "top",
    "vestido longo", "vestido curto", "vestido de festa", "vestido de noiva",
    "terno", "gravata", "sapato", "tênis", "bota", "salto", "chinelo",
    "sandália", "mocassim", "oxford", "alpargata", "slip on",
    "acessórios", "bolsa", "mochila", "carteira", "relógio", "óculos",
    "brincos", "colar", "pulseira", "anel", "cinto",
    "roupa de inverno", "roupa de verão", "roupa de praia", "biquíni", "maiô",
    "moda masculina", "moda feminina", "moda infantil", "moda plus size",
    "tamanho", "numeração", "modelagem", "tecidos", "algodão", "lã", "jeans",
    "seda", "linho", "poliester", "veludo", "mesh", "couro",
    "marca de roupa", "grife", "luxo", "brechó", "second hand", "moda sustentável",
    "fast fashion", "moda circular", "estilo pessoal", "guarda-roupa cápsula",
]

# Beleza e cuidados
BEAUTY = [
    "beleza", "maquiagem", "cabelo", "pele", "trabalhos", "hidratação",
    "esfoliação", "tonificação", "sérum", "protetor solar", "hidratante",
    "creme anti-idade", "retinol", "ácido hialurônico", "vitamina c facial",
    "espinhas", "manchas", "ocelheiras", "rugas", "linhas de expressão",
    "acne", "cravos", "poros", "textura da pele", "pele oleosa", "pele seca", "pele mista",
    "xampu", "condicionador", "máscara capilar", "óleo capilar", "finalizador",
    "corte de cabelo", "tintura", "balayage", "mechas", "luzes", "hidratação capilar",
    "escova", "prancha", "secador", "modelador", "coque", "trança",
    "unhas", "esmalte", "gel", "banho de gel", "alongamento de unha",
    "barba", "barbeador", "corte de barba", "bigode", "sobrancelha", "design de sobrancelha",
    "perfume", "colônia", "desodorante", "essência", "body splash",
    "cuidados com o corpo", "ducha", "banho", "banho gelo", "sauna", "spa em casa",
]

# Esportes individuais (mais)
INDIV_SPORTS = [
    "maratona", "meia maratona", "trail running", "praticar corrida", "corrida de rua",
    "treino de corrida", "aumentar ritmo", "lactato", "vo2max", "cadência",
    "ciclismo", "bicicleta de estrada", "mtb", "gravel", "bike de trilha",
    "escalada", "boulder", "escalada esportiva", "rappel", "rapel",
    "surfe", "prancha", "tubo", "pequeno", "longboard", "stand up paddle",
    "skate", "skate park", "street skate", "longboard skate", "patins",
    "tênis", "raquete", "saque", "forehand", "backhand", "tênis de mesa",
    "badminton", "squash", "racquetball", "bicicleta indoor", "spinning",
    "pilates", "yoga", "pilates solo", "power yoga", "hot yoga",
    "crossfit", "wod", "amrap", "metcon", "levantamento olímpico",
    "musculação", "hipertrofia", "força", "agachamento", "supino", "levantamento terra",
    "natação", "estilos de nado", "crawl", "costas", "peito", "borboleta",
    "atletismo", "lançamento", "arremesso", "salto", "prova combinada",
    "ginástica", "ginástica artística", "solo", "barras", "arco",
    "artes marciais", "judô", "karate", "jiu-jitsu", "muay thai", "boxe",
]

# Cinema brasileiro
BR_CINEMA = [
    "cinema brasileiro", "filme brasileiro", "filme nacional", "novela brasileira",
    "cineasta brasileiro", "diretor de cinema brasileiro", "ator brasileiro",
    "atriz brasileira", "festival de cinema brasileiro", "premiação brasileira",
    "indústria do cinema", "produção audiovisual", "roteiro brasileiro",
    "cidade de deus filme", "central do brasil filme", "auto da compadecida filme",
    "tropa de elite filme", "o auto da compadecida", "selton mello filme",
    "wagner moura filme", "lázaro ramos filme", "rodrigo santoro filme",
    "são paulo filmes", "rio de janeiro filmes", "nordeste filmes", "secca",
    "glauber rocha", "cinema novo", "neorealismo", "estratégia", "tatus",
    "bossa nova filme", "filme de animação brasileiro", "animação brasileira",
    "turma da mônica filme", "o menino e o mundo", "boy and the world",
    "vida de menina", "filme de comédia brasileira", "filme de terror brasileiro",
    "documentário brasileiro", "coletivo", "mosquito", "aquarius", "boca de ouro",
]

# Computação e CS (mais)
CS_TOPICS = [
    "algoritmo", "estrutura de dados", "lista", "pilha", "fila", "árvore",
    "grafo", "hash", "tabela hash", "busca", "ordenação", "backtracking",
    "complexidade", "big o", "recursão", "fibonacci", "fatorial",
    "programação orientada a objetos", "herança", "polimorfismo", "encapsulamento",
    "interface", "abstração", "design patterns", "singleton", "factory",
    "solid", "princípios de design", "refatoração", "código limpo",
    "testes unitários", "tdd", "teste de integração", "mock", "cobertura de código",
    "linguagem de programação", "python", "javascript", "typescript", "java",
    "c#", "c++", "go", "rust", "swift", "kotlin", "ruby", "php",
    "sql", "postgresql", "mysql", "sqlite", "oracle", "sql server",
    "nosql", "redis", "kafka", "rabbitmq", "fila de mensagens",
    "microserviços", "monolito", "eventos", "mensageria", "rest", "graphql",
    "web", "http", "https", "dns", "tcp", "udp", "socket",
    "frontend", "backend", "fullstack", "ci", "cd", "deploy", "monitoramento",
    "containers", "docker", "kubernetes", "cloud", "aws", "azure", "gcp",
    "segurança", "autenticação", "autorização", "tokens", "jwt", "oauth",
]

# Saúde pública
PUB_HEALTH = [
    "sus", "sistema único de saúde", "posto de saúde", "ubs", "upahs",
    "hospital público", "hospitais universitários", "pronto-socorro", "samu",
    "ambulância", "emergência", "urgência", "atendimento médico", "teleconsulta",
    "medicina", "médico", "especialista", "clinico geral", "pediatra", "cardiologista",
    "dermatologista", "ginecologista", "obstetra", "urologista", "neurologista",
    "clínica médica", "exame", "consulta", "junta de saúde", "internação",
    "vacinação", "campanha de vacinação", "calendário vacinal", "vacina",
    "prevenção", "promoção da saúde", "saúde da família", "programa saúde da família",
    "convênio", "plano de saúde", "rede credenciada", "coparticipação", "carência",
    "operação de saúde", "vigilância sanitária", "anvisa", "saúde coletiva",
    "saúde mental pública", "caps", "acolhimento", "tratamento", "reabilitação",
    "atendimento de urgência", "pronto atendimento", "unidade básica de saúde",
    "farmácia popular", "medicamentos", "distribuição de remédios", "fila do sus",
    "ubs da família", "agente de saúde", "agente comunitário",
]

# Gastronomia regional do mundo (mais)
GASTRO_REG = [
    "comida japonesa", "comida coreana", "comida chinesa", "comida tailandesa",
    "comida indiana", "comida mexicana", "comida italiana", "comida francesa",
    "comida espanhola", "comida portuguesa", "comida alemã", "comida árabe",
    "comida libanesa", "comida turca", "comida árabe brasileira", "comida grega",
    "comida do oriente médio", "comida africana", "comida do norte da áfrica",
    "comida marroquina", "comida vegana", "comida vegetariana", "comida fitness",
    "comida de rua", "street food", "comida rápida", "fast food", "deli",
    "prato típico", "prato do dia", "receita típica", "culinária brasileira",
    "culinária nordestina", "culinária mineira", "culinária gaúcha", "culinária baiana",
    "culinária paulista", "culinária carioca", "culinária paraense", "culinária amazonense",
    "culinária goiana", "culinária capixaba", "comida de boteco", "petiscos",
    "churrasco", "espeto", "bucho", "churrasqueira", "parrilha", "fogão a lenha",
    "tempero", "especiarias", "condimentos", "ervas", "molho",
    "benefícios de temperos", "como temperar", "conservas", "geleia", "compota",
    "pão artesanal", "fermentação natural", "massa de pizza", "massa de pão",
]

# História do Brasil (mais)
BR_HISTORY_MORE = [
    "pré-história do brasil", "povos originários", "chegada dos portugueses",
    "descobrimento do brasil", "carta de caminha", "capitanias hereditárias",
    "governo geral", "engenho", "açúcar", "escravidão", "quilombo", "zumbi",
    "bandeirantes", "ciclo do ouro", "minas gerais", "vila rica", "ouro preto",
    "inconfidência", "tiradentes", "período joanino", "dom joão vi", "casa real",
    "independência do brasil", "dom pedro i", "marechal", "primeiro reinado",
    "período regencial", "segundo reinado", "dom pedro ii", "império do brasil",
    "guerra do paraguai", "café", "ciclo do café", "abolição", "leis abolicionistas",
    "república", "proclamação da república", "republica velha", "politica do café com leite",
    "revolução de 1930", "getúlio vargas", "era vargas", "estado novo", "golpe de 1964",
    "ditadura militar", "milagre econômico", "abertura política", "diretas já",
    "constituinte", "constituição de 1988", "redemocratização", "plano real",
    "reatropenção", "pandemia", "bolsonaro", "governo lula", "herença",
    "literatura da república", "republiquetas", "café com leite história",
]

# Pets (mais)
PETS_MORE = [
    "cachorro", "cachorro filhote", "racao para cachorro", "banho em cachorro",
    "adestrar cachorro", "passear com cachorro", "doenças de cachorro",
    "higiene do cachorro", "vacina para cachorro", "castração de cachorro",
    "gato", "gato filhote", "racao para gato", "banho em gato", "brincadeiras de gato",
    "doenças de gato", "vacina para gato", "castração de gato", "areia de gato",
    "caixa de areia", "arranhador", "brinquedo de gato",
    "passaro", "pássaro de estimação", "gaiola", "canário", "papagaio de estimação",
    "pássaro cantor", "alimentação de passaro",
    "coelho de estimação", "alimentação de coelho", "gaiola de coelho",
    "hamster", "rato de estimação", "camundongo", "gerbil", "chinchila",
    "peixe de aquário", "aquário de água doce", "aquário de água salgada",
    "betta", "peixe palhaço", "manutenção de aquário", "filtro de aquário",
    "tartaruga de estimação", "aproveitamento de tartaruga", "alimentação de tartaruga",
    "répteis de estimação", "lagarto de estimação", "cobra de estimação",
    "insetos de estimação", "formiga de estimação", "besouro",
    "animal de estimação idoso", "cuidados com pet idoso", "saúde do pet",
    "pet na viagem", "transportar pet", "hotel para pet", "petsitter",
]

# Horóscopo do dia (mais)
HOROSCOPE_DAILY = [
    "horóscopo dependente", "horóscopo do amor", "horóscopo da sorte",
    "horóscopo de áries hoje", "horóscopo de touro hoje", "horóscopo de gêmeos hoje",
    "horóscopo de câncer hoje", "horóscopo de leão hoje", "horóscopo de virgem hoje",
    "horóscopo de libra hoje", "horóscopo de escorpião hoje", "horóscopo de sagitário hoje",
    "horóscopo de capricórnio hoje", "horóscopo de aquário hoje", "horóscopo de peixes hoje",
    "signo de hoje", "previsão do dia", "previsão semanal", "previsão mensal",
    "previsão do amor", "previsão do trabalho", "previsão da saúde",
    "compatibilidade de signos", "signo compatível", "signo do amor",
    "ascendente significado", "lua no signo significado", "vênus no mapa astral",
    "marte no mapa astral", "júpiter no mapa astral", "saturno no mapa astral",
    "mapa astral completo", "o que é casa 7", "o que é casa 10", "signo em marte",
    "signos mais compatíveis", "signo mais forte", "signo mais raro", "signo mais comum",
    "cristal do signo", "pedra do signo", "elemento do signo", "regente do signo",
]

# Frases e citações
QUOTES_TERMS = [
    "frases motivacionais", "frases de reflexão", "frases de amor", "frases de amizade",
    "frases de vida", "frases de superação", "frases de esperança", "frases de fé",
    "citações famosas", "frases de filósofos", "frases de livros", "frases de filmes",
    "celebração de frases", "pensamentos", "reflexões", "mensagem do dia",
    "frases para status", "frases para foto", "frases para bio", "frases para legenda",
    "frases em inglês", "frases para comemorar", "frases de aniversário",
    "frases de parabéns", "frases de boas-vindas", "frases de motivação para estudar",
    "frases de motivação para trabalhar", "frases de superação emocional",
    "pessoas", "o poder do pensamento", "lei da atração frases", "manifestação",
    "frases de paz", "frases de calmaria", "palavras de conforto", "mensagem de apoio",
]

# Dicas rápidas e utilidades
TIPS = [
    "como economizar dinheiro", "como poupar", "como organizar a vida", "como ser produtivo",
    "como estudar melhor", "técnicas de estudo", "como memorizar", "mnemônicos",
    "como falar bem", "como escrever bem", "como apresentar", "como liderar",
    "como fazer networking", "como conseguir emprego", "como passar em concurso",
    "como emagrecer", "como ganhar massa", "como dormir melhor", "como ter saúde",
    "como economizar energia", "como economizar água", "como reciclar", "como compostar",
    "como limpar a casa", "como organizar a casa", "como decorar", "como planejar uma festa",
    "como viajar barato", "como fazer mochilão", "como economizar na viagem",
    "como tirar fotos bonitas", "como editar vídeos", "como gravar", "como fazer live",
    "como ganhar dinheiro", "como fazer renda extra", "como vender", "como abrir empresa",
    "como declarar imposto", "como investir", "como guardar", "como construir",
    "como fazer um site", "como criar um app", "como programar", "como aprender programação",
    "como aprender inglês", "como aprender espanhol", "como aprender música",
    "como cozinhar", "como fazer pão", "como fazer bolo", "como fazer receita fácil",
    "como cuidar de plantas", "como ter um jardim", "como fazer horta",
    "como ser feliz", "como ter autoestima", "como superar", "como recomeçar",
]

# Build final TOPICS
_topics_extra = (
    GEO_EXTRA + FOOD_WORLD + PERSONALITIES + MOVIES_SERIES + MUSICIANS
    + MEMES_INTERNET + FOOD_EXTRA + FOOTBALL_TEAMS + BRAZIL_STATES
    + BRAZIL_CITIES + UNIVERSITIES + COMPANIES + ANIMALS + HOLIDAYS_DATE
    + DISEASES + RELIGION + SPORTS_EXTRA + CAREER_WRITING + TECH_NEW_2026
    + TRAVEL_MORE + BRAZILIAN_PEOPLE + COUNTRIES_MORE + SCIENCE_NATURE
    + MEDICAL_TERMS + ASIA_POP + GAMES_ALL + MUSIC_STYLES + INSTRUMENTS
    + PHENOMENA + WORLD_TERMS + OFFICE_TOOLS + REGIONAL_FOOD
    + EVERYDAY_SCIENCE + VISUAL_ARTISTS + COUNTRIES_DETAIL + CITIES_WORLD
    + FOOD_MORE + PLANTS + PROFESSIONS + SPORTS_GLOB + VEHICLES + TECH_APPS
    + HISTORY_EVENTS + PHILOSOPHERS + ASTROLOGY + WELLNESS + INTERNET_TERMS
    + SCHOOL_SUBJECTS + IT_TOPICS + MATH_OP + GEOG_MORE + ANIMALS_MORE
    + FICTION_CHARS + SPORTS_NOTFOOT + FAMOUS_PEOPLE + LEISURE
    + ASTRONOMY_OBJ + MODERN_SCI + CHEM_ELEMENTS + WRITERS + SERIES_BR
    + MARKETING_TERMS + ECONOMY_TERMS + LAW_TERMS + HEALTH_LIFESTYLE
    + ANIME_MORE + MOVIES_MORE + MUSIC_ALBUMS + ARTISTS_BR + LANGUAGES
    + RELIGIONS_WORLD + PEOPLES + ARCHITECTURE + ECOLOGY + PSYCHOLOGY
    + SOCIOLOGY + WORLD_HISTORY + SECURITY + FAMILY_REL + COMMUNICATION
    + GEO_POLITICS + AGRI_FOOD + CHILDREN_EDU + ELDERLY + TRANSPORT_MORE
    + WEATHER_ADV + DATA_SCI + TRADING + HANDCRAFT + FESTIVALS + PHARMACY
    + TOURISM_MORE + BOOKS_MORE + STREAMING + BR_POLITICS + ENERGY
    + FASHION_MORE + BEAUTY + INDIV_SPORTS + BR_CINEMA + CS_TOPICS
    + PUB_HEALTH + GASTRO_REG + BR_HISTORY_MORE + PETS_MORE + HOROSCOPE_DAILY
    + QUOTES_TERMS + TIPS
)
for _country, _capital in COUNTRIES_CAPITALS:
    _topics_extra.append(_country)
    _topics_extra.append(f"capital de {_country}")
    _topics_extra.append(_capital)
TOPICS += _topics_extra

# Remover duplicados mantendo ordem
_seen = set()
TOPICS = [t for t in TOPICS if not (t in _seen or _seen.add(t))]

PATTERNS = [
    "o que é {t}",
    "{t} como funciona",
    "como usar {t}",
    "para que serve {t}",
    "benefícios de {t}",
    "como fazer {t}",
    "tipos de {t}",
    "história de {t}",
    "melhores {t} 2026",
    "cuidados com {t}",
    "o que significa {t}",
    "quanto custa {t}",
]


def _gen_queries():
    seen = set()
    out = []
    for t in TOPICS:
        for p in PATTERNS:
            q = p.format(t=t)
            if q in seen:
                continue
            seen.add(q)
            out.append(q)
    return out


def _already(con, query):
    try:
        row = con.execute("SELECT COUNT(*) FROM search_items WHERE query=?", (query,)).fetchone()
        return bool(row and row[0])
    except Exception:
        return False


def main():
    queries = _gen_queries()
    total = len(queries)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    count = int(sys.argv[2]) if len(sys.argv) > 2 else total
    batch = queries[start : start + count]
    print(f"Total de queries geradas: {total} | rodada: {start}..{start + len(batch) - 1}")

    con = sqlite3.connect(str(app.SEARCH_DB))
    ok = skipped = empty = 0
    consec_empty = 0
    for q in batch:
        if _already(con, q):
            skipped += 1
            continue
        try:
            res = app._search_web(q, 5)
        except Exception:
            res = []
        if res:
            app._store_search_results(q, res)
            ok += 1
            consec_empty = 0
        else:
            empty += 1
            consec_empty += 1
        done = ok + empty + skipped
        print(f"[{done}/{len(batch)}] {'OK  ' if res else 'VAZIO'} {q} ({len(res)} res)")
        sys.stdout.flush()
        if consec_empty >= 6 and done < len(batch):
            print("  ...buscador cansou, pausa de 45s...")
            sys.stdout.flush()
            time.sleep(45)
            consec_empty = 0
    con.close()
    print(f"\nFinal: {ok} armazenadas | {empty} sem resultado | {skipped} já existiam")


if __name__ == "__main__":
    main()