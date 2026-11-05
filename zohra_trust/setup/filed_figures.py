"""The figures of the filed June to September 2026 report: the opening stock, each month's purchases and use, and the totals printed on its food statements.

Used by the filed-data test and by the client test data."""

# item: (old_qty, old_amount) of the paper June opening
JUNE_OLD = {"Rice": (50, 2450), "Jawar": (35, 1050), "S. Oil": (3, 450), "Daal": (3, 240), "Sugar": (6, 330), "Salt": (1, 20),
	"Condiments": (11, 2200), "Onion": (20, 400), "C. Oil": (2, 400)}  # fmt: skip
ITEMS = ["Rice", "Jawar", "S. Oil", "Daal", "Sugar", "Tamarind", "Salt", "G. Nut", "Chilli", "Condiments", "Onion", "C. Oil", "T. Soap", "W. Soap"]

# month: (purchases {item: (qty, amount)}, consumed {item: qty}, heads {account: amount}) as printed on the filed statements
MONTHS = {
	6: ({"Rice": (1200, 58800), "Jawar": (600, 18000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (30, 1650), "Tamarind": (30, 2250),
		"Salt": (30, 600), "G. Nut": (30, 3600), "Chilli": (30, 4500), "Condiments": (20, 4000), "Onion": (50, 1000), "C. Oil": (40, 8000),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1050, "Jawar": 450, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 28, "Salt": 30, "G. Nut": 30, "Chilli": 30,
		"Condiments": 15, "Onion": 60, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 15370, "Mutton": 22700, "Fuel": 11780, "Salaries": 11000}),
	7: ({"Rice": (1000, 49000), "Jawar": (300, 9000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (30, 1650), "Tamarind": (30, 2250),
		"Salt": (30, 600), "G. Nut": (40, 4800), "Chilli": (40, 6000), "Condiments": (10, 2000), "Onion": (60, 1200), "C. Oil": (10, 2000),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1085, "Jawar": 465, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 30, "Salt": 31, "G. Nut": 32, "Chilli": 32,
		"Condiments": 16, "Onion": 64, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 8300, "Mutton": 16000, "Fuel": 8000, "Salaries": 11000}),
	8: ({"Rice": (1100, 53900), "Jawar": (800, 24000), "S. Oil": (30, 4500), "Daal": (30, 2400), "Sugar": (32, 1760), "Tamarind": (30, 2250),
		"Salt": (32, 640), "G. Nut": (30, 3600), "Chilli": (30, 4500), "Condiments": (20, 4000), "Onion": (60, 1200), "C. Oil": (24, 4800),
		"T. Soap": (300, 4800), "W. Soap": (300, 4200)},
		{"Rice": 1085, "Jawar": 465, "S. Oil": 32, "Daal": 32, "Sugar": 32, "Tamarind": 32, "Salt": 31, "G. Nut": 32, "Chilli": 32,
		"Condiments": 16, "Onion": 64, "C. Oil": 24, "T. Soap": 300, "W. Soap": 300},
		{"Vegetables": 11990, "Mutton": 20000, "Fuel": 10000, "Salaries": 13000}),
	9: ({"Rice": (1200, 58800), "Jawar": (600, 19998), "S. Oil": (70, 14000), "Daal": (70, 5600), "Sugar": (70, 4375), "Tamarind": (70, 5425),
		"Salt": (65, 1300), "G. Nut": (65, 7800), "Chilli": (65, 11375), "Condiments": (65, 13000), "Onion": (200, 4500), "C. Oil": (60, 12000),
		"T. Soap": (600, 10800), "W. Soap": (600, 9600)},
		{"Rice": 1050, "Jawar": 450, "S. Oil": 30, "Daal": 30, "Sugar": 32, "Tamarind": 30, "Salt": 30, "G. Nut": 30, "Chilli": 30,
		"Condiments": 15, "Onion": 60, "C. Oil": 24, "T. Soap": 600, "W. Soap": 600},
		{"Vegetables": 8815, "Mutton": 16000, "Fuel": 8000, "Salaries": 13000}),
}  # fmt: skip
# month: item: (expenditure, balance_qty, balance_amount) as printed
FILED = {
	6: {"Rice": (51450, 200, 9800), "Jawar": (13500, 185, 5550), "S. Oil": (4500, 3, 450), "Daal": (2400, 3, 240), "Sugar": (1760, 4, 220),
		"Tamarind": (2100, 2, 150), "Salt": (600, 1, 20), "G. Nut": (3600, 0, 0), "Chilli": (4500, 0, 0), "Condiments": (3000, 16, 3200),
		"Onion": (1200, 10, 200), "C. Oil": (4800, 18, 3600), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	7: {"Rice": (53165, 115, 5635), "Jawar": (13950, 20, 600), "S. Oil": (4500, 3, 450), "Daal": (2400, 3, 240), "Sugar": (1760, 2, 110),
		"Tamarind": (2250, 2, 150), "Salt": (620, 0, 0), "G. Nut": (3840, 8, 960), "Chilli": (4800, 8, 1200), "Condiments": (3200, 10, 2000),
		"Onion": (1280, 6, 120), "C. Oil": (4800, 4, 800), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	8: {"Rice": (53165, 130, 6370), "Jawar": (13950, 355, 10650), "S. Oil": (4800, 1, 150), "Daal": (2560, 1, 80), "Sugar": (1760, 2, 110),
		"Tamarind": (2400, 0, 0), "Salt": (620, 1, 20), "G. Nut": (3840, 6, 720), "Chilli": (4800, 6, 900), "Condiments": (3200, 14, 2800),
		"Onion": (1280, 2, 40), "C. Oil": (4800, 4, 800), "T. Soap": (4800, 0, 0), "W. Soap": (4200, 0, 0)},
	9: {"Rice": (51450, 280, 13720), "Jawar": (14998.5, 505, 15649.5), "S. Oil": (6000, 41, 8150), "Daal": (2400, 41, 3280), "Sugar": (2000, 40, 2485),
		"Tamarind": (2325, 40, 3100), "Salt": (600, 36, 720), "G. Nut": (3600, 41, 4920), "Chilli": (5250, 41, 7025), "Condiments": (3000, 64, 12800),
		"Onion": (1350, 142, 3190), "C. Oil": (4800, 40, 8000), "T. Soap": (10800, 0, 0), "W. Soap": (9600, 0, 0)},
}  # fmt: skip
# month: (opening, purchase, available, expenditure, closing) as printed
FILED_TOTALS = {6: (7540, 179150, 186690, 163260, 23430), 7: (23430, 137700, 161130, 148865, 12265),
	8: (12265, 171540, 183805, 161165, 22640), 9: (22640, 224388, 247028, 163988.5, 83040)}  # fmt: skip
FILED_HOSTEL_DAYS = {6: 3000, 7: 3100, 8: 3100, 9: 3000}
MONTH_NAMES = {6: "June", 7: "July", 8: "August", 9: "September"}
HEAD_ACCOUNT = {"Vegetables": "Vegetables", "Mutton": "Mutton", "Fuel": "Fuel"}
