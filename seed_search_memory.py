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

# Build final TOPICS
_topics_extra = (
    GEO_EXTRA + FOOD_WORLD + PERSONALITIES + MOVIES_SERIES + MUSICIANS
    + MEMES_INTERNET + FOOD_EXTRA + FOOTBALL_TEAMS + BRAZIL_STATES
    + BRAZIL_CITIES + UNIVERSITIES + COMPANIES + ANIMALS + HOLIDAYS_DATE
    + DISEASES
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