# txt2evernote

A python script to parse a structured text file and send contents to **Evernote** account

## What does this do?

Parse a structured text file (written in **markdown** or **zim wiki** syntax, and structured with tab levels) and send contents to **Evernote**.

The **structures** of a text file include:

- "filename": corresponds to all lines in the input file.
- "heading1" - "heading6": corresponds to all lines under a heading level.
- "tablevel0" - "tablevel5": corresponds to all lines indented with a certain number of tabs. E.g. "tablevel1" includes all text lines indented with 1 or more tabs.



Better illustrated with an example:


The sample file *sample.md* has these following lines:

```
--------------------------------------------------------------------------------
# The role of horizontal resolution in simulating drivers of the global hydrological cycle

	> AGCMs from the UK Met Officce Hadley Centre: HadGEM1-A at resolutions ranging from
	270 to 60 km and HadGEM3-A ranging from 135 to 25 km. ...... The models exhibit
	a stable hydrological cycle, although too intense compared to reanalyses and
	observations. This overintensity is explained by excess surface shortwave
	radiation, a common error in general circulation models (GCMs). ......
	resolution is increased, precipitation decreases over the ocean and increases
	over the land. ...... his is associated with an increase in atmospheric
	moisture transport from ocean to land, which changes the partitioning of
	moisture fluxes

		- @Demory2013
		- Tags: @HydroCycle
		- Ctime: 2016-01-17 11:19:31


	> The results start to converge at 60-km resolution, which unnderlines the
	excessive reliance of the mean hydrologica ...... al cycle on physical
	parametrization (local unresolved processes) versus model dynamics (large-scale
	resolved processes) in ...... coarser HadGEM1 and HadGEM3 GCMs. ......

		- @Demory2013
		- Tags: @HydroCycle
		- Ctime: 2016-01-17 11:19:31


	> etermine how much we can trust GCM predictions of changes in the hydrological
	cycle in climate change scenarios ......

		- @Demory2013
		- Tags: @None, @HydroCycle
		- Ctime: 2016-01-17 11:28:28


--------------------------------------------------------------------------------
# Changes in precipitation with climate change

	> Hence, storms, whether individual thunderstorms, extratropical rain or snow
	storms, or tropical cyclones, supplied with increased moisture, produce more
	intense precipitation events. ...... With modest changes in winds, patterns of
	precipitation do not change much, but result in dry areas becoming drier
	(generally throughout the subtropics) and wet areas becoming wetter, especially
	in the mid- to high latitudes: with more precipitation per unit of upward
	motion in the atmosphere, ...... , atmospheric circulation weakens, causing
	monsoons to falter. Most models simulate precipitation that occurs prematurely
	and too often, and with insufficient intensity, resulting in recycling that is
	too large and a lifetime of moisture in the atmosphere that is too short, which
	affects runoff and soil moisture

		- @Trenberth2011a
		- Tags: @Climate warming, @Hydrological cycle, @Modelling, @Precipitation,
		@HydroCycle
		- Ctime: 2015-07-21 19:38:28


	> There is a very strong relationship between total column water vapor (TCWV, also
	known as precipitabl (SSTs)  over  the oceans  (Trenberth  et  al.  2005)
	...... The  Clausius-Clapeyron  (Cdescribes  the  water-holding  capacity  of
	the atmosphere as a function of temperature, values are about 7% change for 1 C
	change in tempe ature. ...... SST changes, the TCWV varies with slightly larger
	values  owing  to  the  increase  in  atmosph emperature  perturbations  with
	height,  especially ...... the  tropics ......

		- @Trenberth2011a
		- Tags: @Climate warming, @Hydrological cycle, @Modelling, @Precipitation,
		@HydroCycle
		- Ctime: 2015-07-21 19:45:11



--------------------------------------------------------------------------------
# Multisource Estimation of Long-Term Terrestrial Water Budget for Major Global River Basins

	> For evapotranspiration, in-situ-based estimates rely on networks of flux towers.
	Although these networks are very sparse globally, progress has been made in
	upscaling flux tower estimates to global coverage (Jung et al. 2009). Large-
	scale estimates can also be derived from remote sensing using satellite-
	retrieved radiation fluxes and surface meteorological conditions. The retrieval
	is usually performed using an empirically based, process-based, or energy
	balance model of boundary layer fluxes, such as the Penman Monteith (PM),
	Priestly Taylor (PT), or the Surface Energy Balance System (SEBS) models (Su
	2002) upscaled flux tower-based dataset from the Max Planck Institute (MPI) (
	...... and the SEBSderived estimates ...... using radiation

		- @Pan2012
		- Tags: @None, @HydroCycle
		- Ctime: 2015-05-12 22:40:00


```

To upload these notes to **Evernote** following a structure like this:

- Put all contents in the file to a new **Evernote** notebook. To do this, set "filename" as the **notebook** structure. In this case, the notebook created will be named "sample", the name of the file. 
- Create one **Evernote** note in the newly create notebook for each heading1 section in the file. To do this, set "heading1" as the **title** structure. If multiple heading1s are found, create one note for each heading1 section. In this case, these 3 notes will be created: 
	- "The role of horizontal resolution in simulating drivers of the global hydrological cycle",
	- "Changes in precipitation with climate change",
	- "Multisource Estimation of Long-Term Terrestrial Water Budget for Major Global River Basins".
- In each of the notes created above, use all contents with 1 or more tab indentions as its content. To do this, set "tablevel1" as the **content** structure. In this case, the note "Multisource Estimation of Long-Term Terrestrial Water Budget for Major Global River Basins" will contain the following lines:

> 	> For evapotranspiration, in-situ-based estimates rely on networks of flux towers.
	Although these networks are very sparse globally, progress has been made in
	upscaling flux tower estimates to global coverage (Jung et al. 2009). Large-
	scale estimates can also be derived from remote sensing using satellite-
	retrieved radiation fluxes and surface meteorological conditions. The retrieval
	is usually performed using an empirically based, process-based, or energy
	balance model of boundary layer fluxes, such as the Penman Monteith (PM),
	Priestly Taylor (PT), or the Surface Energy Balance System (SEBS) models (Su
	2002) upscaled flux tower-based dataset from the Max Planck Institute (MPI) (
	...... and the SEBSderived estimates ...... using radiation

		- @Pan2012
		- Tags: @None, @HydroCycle
		- Ctime: 2015-05-12 22:40:00




Putting everything together, to achieve the above:

```
python txt2ever.py inputfile --notebook filename --title heading1 --content tablevel1 -m
```

It's also possible to use same structure keyword for multiple structures, e.g. if "heading1" is set to both **notebook** and **title**, then 3 notebooks will be created using the 3 heading1s, in each notebook, one note is created using the same notebook name, with contents that are tab-indented by 1 level.


## Dependencies

**Geeknote** **maybe** required. And you need to login your **Evernote** account using **Geeknote** first before using this script.


## Usage

```
python txt2ever.py inputfile --notebook NOTEBOOK --title TITLE --content CONTENT -m|-z
```

where:

- `inputfile`: path to text file.
- `NOTEBOOK`: structure to map to **Evernote** notebook name, choose from
	- "filename"
	- "heading1" - "heading6"
	- "tablevel0"- "tablevel5"
	- "given": Give a notebook name. Currently not implemented for command line usage. You can look into the code to do that.
- `TITLE`: structure to map to **Evernote** note title, choose from the above list.
- `CONTENT`: structure to map to **Evernote** note title, choose from the above list except "filename".
- `-m`: specify `inputfile` is in **markdown**
- `-z`: specify `inputfile` is in **zim**


## Acknowledgement

**Geeknote** is used to create notebook and notes.




