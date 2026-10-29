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
Sources: American cancer society, Pubmed, National cancer institute
