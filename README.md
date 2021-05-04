This repo contains the official implementation for the paper [A Framework for Integrating Gesture Generation Models into Interactive Conversational Agents](http://www.ifaamas.org/Proceedings/aamas2021/pdfs/p1779.pdf), published as a demonstration at the 20th International Conference on Autonomous Agents and Multiagent Systems (AAMAS),

by [Rajmund Nagy](https://nagyrajmund.github.io/), [Taras Kucherenko](https://svito-zar.github.io/), [Birger Moëll](https://www.kth.se/profile/bmoell?l=en), [André Pereira](https://sites.google.com/view/andre-pereira-phd), [Hedvig Kjellström](https://www.kth.se/profile/hedvig) and [Ulysses Bernardet](https://research.aston.ac.uk/en/persons/ulysses-bernardet).

-------------

We present a framework for integrating recent data-driven gesture generation models into interactive conversational agents in Unity. 
Our video demonstration is available below:

[![video demonstration](https://i.imgur.com/rqYRYam.png)](https://www.youtube.com/watch?v=jhgUBS0125A)


# Instructions for running the demo
This branch contains our DialogFlow version of our implementation, which requires a functioning [DialogFlow](https://cloud.google.com/dialogflow) project to run.
You may visit the [blenderbot_demo](https://github.com/nagyrajmund/gesturebot/) branch for an alternative version with a built-in Blenderbot chatbot.

Please follow the instructions in [INSTALLATION.MD](INSTALLATION.md) to install and run the project.

# Adapting the components
![](https://i.imgur.com/PSW6a23.jpg)
The source code for the Unity component with DialogFlow integration is available [on this link](https://drive.google.com/file/d/14URIJxO9vyMNHGWbkRyz_jEIiHPGhByM/view?usp=sharing). 


# Acknowledgements
The authors would like to thank [Lewis King](https://lewisbenking.github.io/) for sharing the source code of his JimBot project with us.

# Citation
If you use this code in your research, then please cite it:

```
@inproceedings{Nagy2021gesturebot,
author = {Nagy, Rajmund and Kucherenko, Taras and Moell, Birger and Pereira, Andr\'{e} and Kjellstr\"{o}m, Hedvig and Bernardet, Ulysses},
title = {A Framework for Integrating Gesture Generation Models into Interactive Conversational Agents},
year = {2021},
isbn = {9781450383073},
publisher = {International Foundation for Autonomous Agents and Multiagent Systems},
address = {Richland, SC},
booktitle = {Proceedings of the 20th International Conference on Autonomous Agents and MultiAgent Systems},
location = {Virtual Event, United Kingdom},
series = {AAMAS '21}
}
```
