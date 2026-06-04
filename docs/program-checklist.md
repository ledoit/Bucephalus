# Program checklist (not automated)

Track these outside Bucephalus gates. Check when a line item has evidence (drawing, quote, test report).

## Powertrain

- [ ] V10 block/crank/head architecture frozen (bore, stroke, bank angle, firing order)
- [ ] H2-specific combustion system (injectors, ignition, blow-by, oil dilution strategy)
- [ ] Transverse transaxle torque path and bearing life at peak torque
- [ ] Engine control: λ control, knock, pre-ignition, backfire on decel

## Storage & safety

- [ ] 700 bar tank supplier and TÜV/DOT path chosen
- [ ] Venting, PRD, thermal propagation analysis per tank zone
- [ ] Leak detection, forced ventilation, shutdown states documented
- [ ] Workshop and public refueling interface defined (not gasoline)

## Body / packaging

- [ ] Bay IML surveyed → update `config/*.yaml` `bay` section
- [ ] Crash structure without frunk volume (pedestrian + H2 tank protection)
- [ ] Service access for tanks, injectors, plugs

## Homologation (jurisdiction-specific)

- [ ] Target market list (EU, US, etc.)
- [ ] H2 ICE emissions cycle if applicable in that market
- [ ] Noise, EMC, OBD where required

Bucephalus gates only cover geometry/mass/range consistency — not this list.
