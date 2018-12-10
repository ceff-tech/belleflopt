#Eflows Optimization

Some notes on how to proceed below:

Let's optimize at HUC10 level - looking for each species currently in every HUC10 to have
its preferences met to at least 80% in at least a single HUC 10 in the sample basin

We'll store preferences in Django.

Flow data for each HUC10 will come from natural flows database right now. We'll want to 
figure out in the long run what source we'd use for flows - would it be gage data propagated along
the stream network proportionally? Something else? Is there anything that gives flows
at each stream segment at a daily, weekly, or monthly scale? Ask Ryan and Eric??

We'll make up the species preferences for this project.

We can get a HUC keyed list of species per HUC, then pass that into a function that evaluates
whether needs have been met?

pull PISCES data in region
pull flow data
pull preferences
build EA that relates them - that's not a helpful statement. Brain shutdown.

