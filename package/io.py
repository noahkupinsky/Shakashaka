from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from PIL import Image
import time
import numpy as np
import os
from package.Board import Board
from package.Cell import Cells

SHAKASHAKA_BASE_URL = "https://www.puzzle-shakashaka.com"
PUZZLE_BOARD_CSS_SELECTOR = "#puzzleContainerDiv .board-back"
# Mapping template filenames to Cell types
TEMPLATE_FILENAME_TO_CELL_TYPE = {
    'black': Cells.BLACK,
    'undecided': Cells.UNDECIDED,
    'zero': Cells.ZERO,
    'one': Cells.ONE,
    'two': Cells.TWO,
    'three': Cells.THREE,
    'four': Cells.FOUR,
    'lower_left': Cells.LOWER_LEFT,
    'lower_right': Cells.LOWER_RIGHT,
    'upper_left': Cells.UPPER_LEFT,
    'upper_right': Cells.UPPER_RIGHT,
    'empty': Cells.DECIDED_EMPTY
}
WHITE_THRESHOLD = 240
CELL_SIZE = 25
GRID_LINE_WIDTH = 1

CHAR_TO_CELL = {cell.char: cell for cell in Cells.ALL}

def generate_shakashaka_puzzle_url(grid_size):
    assert grid_size in [5, 10, 15, 20, 25], "Grid size must be one of [5, 10, 15, 20, 25]"
    size_parameter = (grid_size / 5) - 1
    return f"{SHAKASHAKA_BASE_URL}/?size={size_parameter}"

def capture_puzzle_board_screenshot(puzzle_url):
    # Setup Chrome in headless mode
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=2000,2000")  # Set desired size
    driver = webdriver.Chrome(options=options)

    driver.get(puzzle_url)
    time.sleep(1)  # wait for content to load

    board_element = driver.find_element(By.CSS_SELECTOR, PUZZLE_BOARD_CSS_SELECTOR)
    location = board_element.location_once_scrolled_into_view
    size = board_element.size

    driver.save_screenshot("full_page.png")

    x = location['x']
    y = location['y']
    width = size['width']
    height = size['height']
    image = Image.open("full_page.png")
    cropped = image.crop((x, y, x + width, y + height))
    
    os.remove("full_page.png")

    driver.quit()
    
    return np.array(cropped)

def extract_cells_from_board(image):
    grid_size = (image.shape[0] - GRID_LINE_WIDTH) // (CELL_SIZE + GRID_LINE_WIDTH)  # grid lines are 1 wide, so we add 1 to the cell size
    # grid lines are 1 wide, so we add 1 to the cell size
    cells = []
    for x in range(grid_size):
        column = []
        for y in range(grid_size):
            cell = image[
                y * (CELL_SIZE + GRID_LINE_WIDTH) + GRID_LINE_WIDTH : (y + 1) * (CELL_SIZE + GRID_LINE_WIDTH),
                x * (CELL_SIZE + GRID_LINE_WIDTH) + GRID_LINE_WIDTH : (x + 1) * (CELL_SIZE + GRID_LINE_WIDTH)
            ]
            column.append(cell)
        cells.append(column)

    return cells

def load_templates():
    folder = os.path.join(os.path.dirname(__file__), 'templates')
    
    templates = {}
    for filename in os.listdir(folder):
        if filename.endswith(".png"):
            name = filename[:-4]
            template = Image.open(os.path.join(folder, filename)).convert("RGB")
            cell_type = TEMPLATE_FILENAME_TO_CELL_TYPE[name]
            templates[cell_type] = np.array(template)
    
    return templates

def classify_cells(cells):
    templates = load_templates()
    template_shape = next(iter(templates.values())).shape

    def classify_cell(cell):
        best_match = None
        best_score = float('inf')

        for cell_type, template in templates.items():
            score = np.mean((cell - template) ** 2)  # Mean Squared Error
            if score < best_score:
                best_score = score
                best_match = cell_type

        return best_match
            
    board = []
    
    for column in cells:
        board_column = []
        for cell in column:
            if cell.shape != template_shape:
                raise ValueError(f"Cell shape {cell.shape} does not match template shape {template_shape}")
            board_column.append(classify_cell(cell))
        board_column.reverse()
        board.append(board_column)

    return board
            

def crop_board_image(image):
    # start at the middle left of the image and find the first non-white pixel
    height, width, _ = image.shape
    mid_y = height // 2
    mid_x = width // 2
    left = 0
    right = width - 1
    top = 0
    bottom = height - 1
    while np.all(image[mid_y, left] >= WHITE_THRESHOLD):
        left += 1
    while np.all(image[mid_y, right] >= WHITE_THRESHOLD):
        right -= 1
    while np.all(image[top, mid_x] >= WHITE_THRESHOLD):
        top += 1
    while np.all(image[bottom, mid_x] >= WHITE_THRESHOLD):
        bottom -= 1
        
    return image[top:bottom + 1, left:right + 1]
            
def image_to_board(image):
    cells = extract_cells_from_board(image)
    board = classify_cells(cells)
    
    return Board(board)

def scrape_board(size):
    url = generate_shakashaka_puzzle_url(size)
    image = capture_puzzle_board_screenshot(url)
    return image_to_board(image)

def load_board_from_image(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image file '{path}' does not exist")
    
    pil_image = Image.open(path).convert("RGB")
    image = np.array(pil_image)
    cropped = crop_board_image(image)
    return image_to_board(cropped)

def load_board_from_text(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Text file '{path}' does not exist")
    
    with open(path, 'r') as file:
        lines = file.readlines()
        
    lines.pop()
    lines.pop(0)
    lines = [line[::2] for line in lines]  # remove print spacing
    lines = [[line[i] for i in range(len(line)) if line[i] in CHAR_TO_CELL] for line in lines]
    lines.reverse()
    
    grid = [[None for _ in range(len(lines))] for _ in range(len(lines))]
    
    for y, line in enumerate(lines):
        for x, char in enumerate(line):
            if char in CHAR_TO_CELL:
                grid[x][y] = CHAR_TO_CELL[char]
            else:
                raise ValueError(f"Unknown character '{char}' in text file")
    return Board(grid)
    
    