# Melanoma Simulator

This project is an interactive melanoma growth simulator built with Python and Pygame.

I created it to explore how melanoma can grow, mutate, and form different cell populations over time.

The simulator includes:
- melanoma clone growth
- mutation-based cell lineages
- normal skin cell types
- tumor depth and invasion
- a top-down tumor view
- a magnified skin cross-section
- blood vessel contact
- clone identity information

## screenshots

<img width="1627" height="814" alt="Screenshot 2026-10-29 at 7 20 35 AM" src="https://github.com/user-attachments/assets/0815ffbf-86ae-401f-8fe4-1dc4ff012ea3" />

### magnified cross section of skin

<img width="398" height="504" alt="Screenshot 2026-10-29 at 7 21 35 AM" src="https://github.com/user-attachments/assets/9df3f819-68e3-4767-a568-59dafc0bad53" />

### clone identity card

<img width="365" height="315" alt="Screenshot 2026-10-29 at 7 20 49 AM" src="https://github.com/user-attachments/assets/f238b45d-88da-4898-b761-4fb9b7b15693" />



## Controls

- `SPACE` = pause / resume
- `N` = advance one step
- `H` = switch between clone view and heat map
- `M` = turn the magnified cut view on / off
- `R` = reset the simulation

## How to run

Install this:

```bash id="o2lcxy"
pip install pygame-ce
```

After that run:

```bash id="qop4yz"
python3 main.py
```

## Purpose

The goal of this project is to combine biology and programming in a visual simulation.

I used the project to simply model and experiment ideas such as:
- clonal evolution
- independent mutation events
- tumor heterogeneity
- melanoma invasion through skin layers
- how different cell populations compete for space

## important

This is an educational simulation, not a medical or clinical tool.

The growth rates, mutation probabilities, tissue dimensions, and simulation steps are simplified and are not meant to predict real melanoma progression, survival, or treatment response.

## Development

Built with Python and Pygame.

AI tools were used during development for part of the coding and debugging. 
The project design, biological questions, testing, and changes to the simulation were developed 
entireley with my own experimentation and decisions as well as research and personal interest on the subject.

## Sources

American Cancer Society, PubMed, National Cancer Institute, my high school biology teachers.
