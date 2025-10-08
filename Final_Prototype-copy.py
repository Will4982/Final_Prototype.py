import pygame
import sys
import random
 
pygame.init()
 
# --- Screen setup ---
WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyber Quest – Prototype")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28)
 
# --- Colors ---
BLACK = (0,0,0)
WHITE = (255,255,255)
BLUE = (50,200,255)
RED = (200,50,50)
GREEN = (50,255,50)
YELLOW = (255,220,0)
PURPLE = (180,0,255)
GRAY = (60,60,60)
 
# --- Game state ---
game_state = "play"   # "play", "question", "game_over", "win"
 
# --- Player setup ---
player = pygame.Rect(60, HEIGHT-100, 40, 50)
player_vel = [0,0]
on_ground = False
can_double_jump = True
facing = 1
hp = 100
lives = 3
 
# --- Projectiles ---
projectiles = []
 
# --- Levels ---
levels = [
    {   # Level 1
        "spawn": (60, HEIGHT-100),
        "enemies": [(400, HEIGHT-90, [350, 500])],
        "collectibles": [(600, HEIGHT-120)],
    },
    {   # Level 2
        "spawn": (60, HEIGHT-100),
        "enemies": [(300, HEIGHT-90, [250, 500]), (600, HEIGHT-90, [550, 750])],
        "collectibles": [(200, HEIGHT-120), (700, HEIGHT-120)],
    }
]
level_index = 0
 
# --- Enemy & collectible states ---
enemies, enemy_dirs, enemy_alive = [], [], []
collectibles, collected = [], []
portal = None
 
# --- Questions ---
tf_questions = [
    ("Your cell phone cannot be infected by malware.", "False"),
    ("Two-factor authentication improves security.", "True"),
    ("Using the same password everywhere is safe.", "False"),
]
final_questions = [
    ("Which is the BEST way to verify a suspicious email?",
     ["Click the link", "Reply to sender", "Verify via official channel"],
     "Verify via official channel"),
    ("What does phishing try to do?",
     ["Improve battery life", "Steal sensitive info", "Fix malware"],
     "Steal sensitive info"),
]
 
# --- Question room state ---
current_question = None
current_answers = []
correct_answer = None
question_callback = None
question_buttons = []
 
def reset_level(index):
    global player, player_vel, on_ground, can_double_jump, hp
    global enemies, enemy_dirs, enemy_alive, collectibles, collected, portal
    level = levels[index]
    player.topleft = level["spawn"]
    player_vel = [0,0]
    on_ground = False
    can_double_jump = True
    hp = 100
    enemies = [pygame.Rect(x,y,40,40) for x,y,_ in level["enemies"]]
    enemy_dirs = [-1 for _ in enemies]
    enemy_alive = [True for _ in enemies]
    collectibles = [pygame.Rect(x,y,20,20) for x,y in level["collectibles"]]
    collected = [False for _ in collectibles]
    portal = None
 
def start_question(question, answers, correct, callback):
    global game_state, current_question, current_answers, correct_answer, question_callback, question_buttons
    game_state = "question"
    current_question = question
    current_answers = answers
    correct_answer = correct
    question_callback = callback
    question_buttons = []
    for i,ans in enumerate(answers):
        rect = pygame.Rect(150, 200+i*70, 500, 50)
        question_buttons.append((rect, ans))
 
def handle_answer(choice):
    global game_state
    result = (choice == correct_answer)
    game_state = "play"
    if question_callback:
        question_callback(result)
 
def show_end_screen(title, button_text, callback):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill(GRAY)
    screen.blit(overlay, (0,0))
 
    title_surf = font.render(title, True, WHITE)
    screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 150))
 
    rect = pygame.Rect(WIDTH//2-100, 250, 200, 50)
    pygame.draw.rect(screen, WHITE, rect, border_radius=5)
    text = font.render(button_text, True, BLACK)
    screen.blit(text, (rect.x+rect.w//2-text.get_width()//2, rect.y+10))
 
    return rect, callback
 
# --- Init first level ---
reset_level(level_index)
 
# --- Main loop ---
running = True
while running:
    clock.tick(60)
    clicked = False
    click_pos = None
 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked = True
            click_pos = event.pos
 
    keys = pygame.key.get_pressed()
 
    # --- GAMEPLAY STATE ---
    if game_state == "play":
        # Movement
        if keys[pygame.K_LEFT]:
            player_vel[0] = -5
            facing = -1
        elif keys[pygame.K_RIGHT]:
            player_vel[0] = 5
            facing = 1
        else:
            player_vel[0] = 0
 
        if keys[pygame.K_UP]:
            if on_ground:
                player_vel[1] = -12
                on_ground = False
                can_double_jump = True
            elif can_double_jump:
                player_vel[1] = -12
                can_double_jump = False
 
        if keys[pygame.K_SPACE]:
            if len(projectiles) < 5:
                bullet = pygame.Rect(player.centerx, player.centery, 10, 5)
                projectiles.append((bullet, facing, 0))
 
        # Gravity
        player_vel[1] += 0.6
        if player_vel[1] > 10: player_vel[1] = 10
 
        # Player update
        player.x += player_vel[0]
        player.y += player_vel[1]
        if player.bottom >= HEIGHT-40:
            player.bottom = HEIGHT-40
            player_vel[1] = 0
            on_ground = True
        else:
            on_ground = False
 
        # Enemies
        for i,e in enumerate(enemies):
            if not enemy_alive[i]: continue
            e.x += enemy_dirs[i]*2
            lo,hi = levels[level_index]["enemies"][i][2]
            if e.left < lo or e.right > hi:
                enemy_dirs[i] *= -1
            if player.colliderect(e):
                lives -= 1
                hp = 100
                player.topleft = levels[level_index]["spawn"]
                if lives <= 0:
                    game_state = "game_over"
 
        # Projectiles
        new_projectiles = []
        for bullet,dir,dist in projectiles:
            bullet.x += dir*10
            dist += 10
            if dist < 200:
                for i,e in enumerate(enemies):
                    if enemy_alive[i] and bullet.colliderect(e):
                        enemy_alive[i] = False
                new_projectiles.append((bullet,dir,dist))
        projectiles = new_projectiles
 
        # Collectibles
        for i,c in enumerate(collectibles):
            if not collected[i] and player.colliderect(c):
                collected[i] = True
                q,ans = random.choice(tf_questions)
                start_question(q, ["True","False"], ans,
                    lambda correct: None)
 
        # Portal spawn
        if all(collected) and not any(enemy_alive) and portal is None:
            portal = pygame.Rect(700, HEIGHT-100, 40, 60)
 
        if portal and player.colliderect(portal):
            q,choices,correct = random.choice(final_questions)
            def portal_callback(correct_ans):
                global level_index, game_state
                if correct_ans:
                    if level_index+1 < len(levels):
                        level_index += 1
                        reset_level(level_index)
                    else:
                        game_state = "win"
                else:
                    pass  # wrong answer = lose life (you can add penalty here)
            start_question(q, choices, correct, portal_callback)
 
    # --- DRAWING ---
    screen.fill(BLACK)
 
    if game_state == "play":
        # Ground
        pygame.draw.rect(screen, GREEN, (0, HEIGHT-40, WIDTH, 40))
 
        # Player
        pygame.draw.rect(screen, BLUE, player)
 
        # Enemies
        for i,e in enumerate(enemies):
            if enemy_alive[i]:
                pygame.draw.rect(screen, RED, e)
 
        # Collectibles
        for i,c in enumerate(collectibles):
            if not collected[i]:
                pygame.draw.rect(screen, YELLOW, c)
 
        # Portal
        if portal:
            pygame.draw.rect(screen, PURPLE, portal)
 
        # Projectiles
        for bullet,_,_ in projectiles:
            pygame.draw.rect(screen, WHITE, bullet)
 
        # HUD
        hp_bar = pygame.Rect(10,10,hp*2,20)
        pygame.draw.rect(screen, RED, (10,10,200,20))
        pygame.draw.rect(screen, GREEN, hp_bar)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        screen.blit(lives_text,(10,40))
 
    elif game_state == "question":
        screen.fill(GRAY)
        q_surf = font.render(current_question, True, WHITE)
        screen.blit(q_surf, (50, 100))
        for rect, ans in question_buttons:
            pygame.draw.rect(screen, WHITE, rect, border_radius=5)
            text = font.render(ans, True, BLACK)
            screen.blit(text, (rect.x+10, rect.y+10))
            if clicked and rect.collidepoint(click_pos):
                handle_answer(ans)
 
    elif game_state == "game_over":
        rect,cb = show_end_screen("YOU DIED", "Respawn", lambda: reset_level(level_index))
        if clicked and rect.collidepoint(click_pos):
            cb()
            game_state = "play"
 
    elif game_state == "win":
        rect,cb = show_end_screen("YOU WIN", "Restart", lambda: reset_level(0))
        if clicked and rect.collidepoint(click_pos):
            cb()
            game_state = "play"
            level_index = 0
            lives = 3
 
    pygame.display.flip()
 
pygame.quit()
sys.exit()