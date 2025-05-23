# Ellexium’s (aka Day420) Advanced Vehicle Selector



- Essentially a completely, scratch built concept showcasing a re-imagination of the in-game vehicle selector UI.


# How to Install?

Copy the EllexiumModManager folder from the EllexiumModManager zip attached to this post and put it in your Mods folder.


Don't take the contents out of the folder. Put the folder in the mods directory as is. After that, double click the EllexiumModManagerLauncher.bat file to run it.

Ensure that BeamNG.drive is always running before you run the EllexiumModManager.bat file. You don't have to be loaded into a map or anything, the game just needs to be running so the application can look through the game's files and properly display default vehicle configurations. It does not modify any of the game's files. The first launch will be very slow as it copies the files initially, but subsequent runs will be faster since the files will be copied already.


Some features include:

- Seamless and much faster than default switching between the game and the selector using a customizable shortcut or the switcher window.

- Spawning multiple vehicles at once quickly and easily through a graphical list

- Favorites system so you can “pin” specific configurations within vehicles that you like

- Faster configuration searching: By toggling the “Search Mode”, you can very quickly find configurations by looking through vehicles instead of one by one in a giant list

- Filter/Search by zip – this allows for searching by zip right through the selector to quickly find a mod – this also helps with finding configurations very quickly if the mod isn’t a standalone vehicle.

- Search for configuration within the specific vehicle – there is an additional search bar within the configurations view that allows for searching for specific configurations within one vehicle – also with the option of looking through all zips or a specific zip, seeing which zip/mod configurations are apart of.

- Deleting mods and configurations straight through the selector by right clicking within configurations view – this allows you to delete a mod right from the selector. This is especially useful coupled with being able to search by zip and allows for a visual representation of vehicles you have in your mods/repo folder.

- The ability to hide vehicles from the selector and isolate mods without deleting them without using the slow in-game menu.

- The ability to deeply customize the primary color of the selected configuration before spawning vs. having to pick colors from a predetermined list in the in game selector.




# Disclaimer

This is more of an experiment born out of me being tired of waiting forever to switch between playing the game and choosing a new vehicle, and it may have a few bugs here and there and a few quirks as well (such as the Unpacked Mods filter not being finished). It was made completely with Python/Tkinter and all the source code is provided in the download. Technically you could just run the included python files if you wanted to but launching it from a .bat makes it easy for anyone to run.

There’ll likely be a "Security Warning" from windows when running it for the first time, and Windows Defender or other antivirus software may incorrectly flag it as a virus. All the code is provided in human readable form as a .py file and the .bat file isn't much more than a simple text file with to lines of code to start the mod, so if it raises your suspicions feel free to inspect them. If for some reason this mod appears available for download somewhere else, avoid downloading from other sites/sources, and only download it from this thread on the BeamNG.drive forums.




# How does it work?

Copying Specific Files

- It copies only specifically the .json files and related image files (very small versions) needed to present the vehicles and their information from the zip files contained in the Mods, Repo and BeamNG vehicles folder, and stores them in the Data folder contained in the ModManager folder. Due to this, loading configurations and other operations are very fast, and the copied files are so small that it’s not likely to have too much of a storage impact (for reference, I have close to 116 GB of mods and the copied files needed from every zip comes up to about 362 MB). This process is completely automatic and happens in the background, and if you delete a mod these files will automatically be deleted without your intervention on the next run of the application.

Swapping Between the selector and BeamNG.drive

- The application simply runs alongside BeamNG, and allows you to switch between them quickly by offering both a customizable binding (Ctrl+Y by default) or a little unobtrusive transparent button styled like a BeamNG UI app (accessed through the "Show Switcher" button) that stays on top of both the selector and the BeamNG window. It does not replace the BeamNG vehicle selector or UI components. You can very easily use the regular in-game selector at the same time as it does not alter the functionality of the game or alters its files in any way. If you would like to delete the app, just go into your mods folder and delete the provided EllexiumModManager folder - that's it. Be aware that this comes at the cost of a small amount of RAM, but it’s very minor compared to the amount of RAM BeamNG uses, and there's little to no GPU or CPU impact by having the application sitting in the background.

Spawning/Deleting Vehicles

- When you spawn or replace a vehicle/traffic, the app detects whether the game is running or not, and switches to it, uses the shortcut binding from EllexiumModManagerInput.zip, and runs appropriate commands from dynamically updated lua files in the /data folder. Originally it used to be clunkier and open the console, but this new method makes it more robust, faster, more reliable, and much closer looking (visually) to the default vehicle selector, with the added benefit that comes from the snappiness of the Mod Manager.



# Tips

- If you have over 1100 mods, it will disable the labels under each picture on the main screen to prevent visual cutoff and glitches and preserve performance. Hovering over each preview will provide you with information about the mod on the sidebar as usual.

- If you have the issue where you see a preview and don’t know where it came from or what it belongs to, hovering over the image will show you the corresponding zip file on the sidebar or if it’s a config with no zip, it the label will be blue and you’ll see which folder in your user vehicles folder it belongs to.

- It’s very likely that if the application appears to be frozen, it’s doing something (like loading or copying files) on the background. Give it some time before declaring it frozen and trying to close it, especially when starting up. I have tried to add a loading indicator, but it may be hidden behind the window.



# Final Notes

This project has mainly been a learning experience for me, and I didn’t expect it to get this far, or even evolve into a GUI (it used to just be a simple script that would list zip files for me), so I’ve surprised myself by the fact that I’ve gotten this far at all. I’d like to reiterate that this is an ongoing WIP experiment that is highly likely to get completely rewritten from scratch in the future. It has bugs, and quirks and planned features, but I’ve tested it very thoroughly to make sure that despite that it enhances my experience as much as possible, so it should for you too.

Honestly, I wasn’t planning to share this since it's more of a concept than anything, but as I added more to it, I thought, why not? Maybe other people could benefit from this, so I did.

Please do not re-upload this anywhere else or download it from other sites/sources, only get it from here. The BeamNG forums are the only place I upload my mods to, anyplace else hosting this or any other mods from me are illegitimate.

Thanks for reading if you got this far, and feel free to suggest features related to the selector or report bugs, as although I’ve spent as much time as I could have testing it thoroughly, there may be bugs I might not be aware of.

Hope you enjoy if you give it a try!




# Update History (from newest to oldest)
# ---------------------------------------
# Version: 0.2.0 (Public Experimental Snapshot - 15th Release | May 17, 2025


- Added smooth animations to buttons, windows appearing and closing, and tooltips.

- Added an optional Pinned favorites category to the main list so you can immediately see which vehicles and configs you have favorited.

- Added an option to the settings menu to allow you to customize which categorization mode you'd like to have on startup.

- Added an option to the settings menu that allows you to keep the details list open when spawning and replacing configurations.

- Added an option that allows you to clear BeamNG's vehicle cache. This will clean the vehicle cache specifically in a targeted way that should help with vehicle material and texture issues without having to reload the cache for everything non-vehicle related else as well.

- Added options to the Player Vehicle and Spawn Vehicle drop downs that allow for: Spawning/Replacing with a random Car specifically, or Spawning/Replacing with a random Bus/Truck/Van specifically.

- Added options to the Spawn Vehicles dropdown to spawn just parked traffic vehicles, or spawn just moving traffic vehicles.

- Added a label to the top of the details list that indicates if the list is filtered and the type of filter that may be applied.

- Made category orders more consistent overall - so when searching or filtering the categories are highly likely to remain in the same order throughout the entire session.

- When the categorization mode is None, and installation date sorting isn't applied, the main list ordering will more closely resemble vanilla BeamNG's.

- Improved loading mechanisms when hiding and unhiding categories.

- Optimized configuration loading in many cases in the details list.

- Fixed cases where the notification window could get stuck on "Checking for changes..." and not go away.

- Fixed cases where some vehicles and configs would be thrown under unknown categories and have their information missing by reorganizing the prioritization order of data loading.

- Fixed bugs that caused the main list of vehicles to become invisible in certain cases after resizing or changing the UI scale.

- Fixed the "Remove All Other Vehicles" and "Spawn Traffic and Parked Vehicles" buttons not working correctly due to changes from the 0.35 BeamNG.drive update.

- Fixed many cases where the main list visually glitching out and tearing frames could occur if scrolling was done quickly.




# Version: 0.1.9 (Public Experimental Snapshot - 14th Release | April 13, 2025)


- Added a new customizable shortcut (Ctrl+Y by default) to the Mod Manager that makes it feel more seamless with the game. No need to use the Switcher button to switch back and forth (unless you'd like to. The shortcut can be found in game in the Menu Navigation section if you'd like to change it.

- Added an option to the settings menu that allows you to set the UI scale to the either Small Medium or Large.

- Added the ability to freely resize/maximize the application and change the window dimensions without having to go through the process of restarting as the code for resizing has been completely reworked.

- Added an option to display the Jump to page button on the bottom of the configuration list view instead of the top.

- Added an Esc shortcut to the different views and menus. Pressing Escape generally clears a search or goes back to the previous list or closes the modal window being used (for eg. the Hidden Vehicles Window or the Color customization window).

- Added scrolling to the sidebar information in detailed configuration list so that when descriptions and other data gets too long to fit on the sidebar, it's possible to scroll through it instead of having it get cut off.

- Completely reworked the settings menu to make it easier to understand what everything does and changes and made the settings saving mechanisms more robust so they persist through different sessions.

- Partially reworked the data structures to better identify JSON information to prevent vehicles from showing up under the "Unknown" category unnecessarily. 

- Fixed and refactored the code for opening configuration lists and swapping between Favorites and View all is now significantly faster and more robust. This should eliminate recovery restarting occasionally happening when opening a configurations details as well. 

- Fixed a case where the color picker would fail to load some of the values properly and produce an error message.

- Fixed cases where the folder names within the zips could have been improperly separated causing one vehicle to show up under multiple vehicle previews.

- Fixed cases where favorites could sometimes appear duplicated in the favorites view of the configuration list

- Loading time before and after the first run has been reduced significantly. An post first time run initialization sequence has essentially been cut down to a 1/4 of what it used to be before through the introduction of new data caching mechanisms.

- The installation process has been simplified and now only requires copying one folder (EllexiumModManager) to the mods folder.

- The download size for zip has been reduced.

- Many other bugs/issues and other quirks have been fixed and addressed. However, this list would get very long if they were all stated here. Essentially, the manager should be several times more stable and free from bugs than it was before in a general sense.




# Version: 0.1.7.3 (Public Experimental Snapshot - 13th Release | March 18, 2025)


- Made the spawning/replacing/saving/deleting processes more reliable by running a check to make sure the commands have actually been run. If this check fails, it will attempt to run the commands a few more times. This should help with cases where the buttons meant to interact with the game seemingly don't do anything sometimes. 

- Changed the wording on the resize window to make the instructions more clear and changed the name of the related button to "Change Window Size"



# Version: 0.1.7.2 (Public Experimental Snapshot - 12th Release | March 16, 2025)


- Fixed memory leaks associated with reloading the main list. The memory footprint of the mod has now been reduced drastically, especially when collapsing categories, searching, filtering, and more.



# Version: 0.1.7.1 (Public Experimental Snapshot - 11th Release | March 15, 2025)


- Fixed cases where customizing a config color would spawn the previous vehicle sometimes.



# Version: 0.1.7 (Public Experimental Snapshot - 10th Release | March 15, 2025)


- Added an "Isolate Mod" feature (showcased in video) - this adds a new button to the Configuration Details window that moves the mod to a folder within your userfolder instead of completely removing it, separating it from the rest of the mods and preventing the mod from being loaded into the game without deleting it. This is very similar to "Disabling mods" using the in game menu, but this is far cleaner as the isolated mods are kept separate.

- Added a color picker window (showcased in video) - this allows you to fine tune the primary color including (clearcoat, roughness, etc) before spawning or replacing a vehicle from the configurations view.

- Added the option "Double Click to Spawn" to the settings menu that allows you to change double click behavior in the configurations list.  By default, middle clicking a configuration immediately spawns it, and double clicking it adds it to the spawn queue, but there is now a setting that allows for these actions to be swapped.

- Added an option  "Display Vehicle Folder Names" to the settings menu that shows the vehicle folder names under previews that makes it even easier to find vehicle folders with no preview images.

- Fixed a few bugs that prevented the main list from getting updated cleanly when a data refresh was triggered.

- Fixed cases where the red selection highlight that appears when hiding vehicles could change back to white prematurely while scrolling.



# Version: 0.1.6 (Public Experimental Snapshot - 9th Release | March 13, 2025)


- Changed the launcher from .vbs to .bat since this seems to work better for launching the mod manager.

- Added a "Hidden Vehicles" feature (showcased in the video) - this allows you to prevent vehicles you choose from showing up in the main list (decluttering it). Please note: this does not disable the mods or remove them from any folders - this is purely visual.

- Added a Jump to page button in the configuration view (showcased in the video) - this allows you to jump between pages of configurations for vehicles with more than 50 configs.

- Clicking on a vehicle in the main list now puts a blue highlight around it so that it's easier to find what vehicle you clicked on after switching to the selector or spawning a car.

- The folder name is now shown at the bottom of the sidebar underneath the zips associated with a vehicle.

- In very rare cases, clicking to open a vehicle configurations list may send the mod manager in a loop of closing/opening the configurations display. Instead of this, the application now restarts itself to prevent this loop from happening.



# Version: 0.1.5.2 (Public Experimental Snapshot - 8th Release | March 7, 2025)


- Fixed value sorting breaking if the number of configs went over 50 and you went to the next page.



# Version: 0.1.5.1 (Public Experimental Snapshot - 7th Release | March 7, 2025)


- Fixed cases where the spawn queue wouldn't work if there was a custom config in it



# Version: 0.1.5 (Public Experimental Snapshot - 6th Release | March 7, 2025)


- Fixed instances where clicking scan and refresh from settings would leave the main list of vehicles blank if there was a search active.

- Configurations are now sorted by Value similarly to the vanilla vehicle selector.

- Added an option "Show Configs Without Images: in the settings menu to toggle hiding configurations with no preview images for a cleaner UI. From my observation, this mainly hides auxillary debug content, althought this is not what this option explicitly does. (If you already have the mod and you simply replace the .exe file, it may still be on by defaut. Simply click the settings button, and click the new option to toggle the new feature.

- Fixed a bug where where the sidebar info wouldn't fully update if another configuration was selected.

- Fixed hidden categories becoming unhidden during a consecutive search on the main list.

- Instead of an exe, the mod is now started with EllexiumModManagerLauncher.vbs. I've observed that Windows Defender doesn't seem to falsely flag it with this combination, so this is the reasoning for the change. There'll still likely be a warning when running the .vbs file for the first time, but you should be able to just click "Don't show again" or similar and it shouldn't trigger antiviruses. This comes with the disadvantage of having to put a copy of Python in the zip file as well (which makes the download size a little bigger), but I think not constantly having antiviruses harassing the mod is worth it.



# Version: 0.1.4.1 (Public Experimental Snapshot - 5th Release | March 5, 2025)


- Removed dependency on opening console. The application no longer needs to copy or paste commands to the console - this removes several issues with spawning/replacing/deleting and makes it seamless and fast. No more random camera switching or other turning cars on/off. Clicking a delete/Spawn/replace button means it just switches to the game and spawns the cars. This should make the experience much better overall and make using the selector feel easier, faster and more reliable.

- Fixed a bug where switching through pages in the configuration view would sometimes not show all configurations due scroll position not being properly reset.

- Fixed a bug in the Favorites configuration view mode where removing a favorite on a page other than page 1 would not refresh the view properly

- Fixed instances where the loading... notification may get stuck on the screen indefinitely in some scenarios.



# Version: 0.1.3 (Public Experimental Snapshot - 4th Release | March 4, 2025)


- Improved Text File Decoding with UTF-8. There were several areas throughout the application where UnicodeDecodeErrors where happening due to lack of UTF-8 decoding. This caused configurations/previews to not show up in many cases.



# Version: 0.1.2 (Public Experimental Snapshot - 3rd Release | March 4, 2025)


- The vanilla vehicles directory location is now determined by the location of the BeamNG.drive.exe file located within the BeamNG.drive installation directory. This means that the folder no longer has to be selected at the start - just make sure BeamnNG.drive is running whenever Mod Manager is run.

- Switching to BeamNG when spawning, deleting, replacing, etc is a little faster now

- Add Mod(s) option and Choose new User vehicles folder options have been removed as they are remnants of older code and no longer necessary with the dynamic detection of folders

- The Initializing Data and Populating Caches loading notifications should no longer be obscured by the completely white unloaded GUI on startup



# Version: 0.1.1 (Public Experimental Snapshot - 2nd Release | March 3, 2025)


- Fixed "Replace Current" button on the sidebar spawning a new vehicle instead of actually replacing the vehicle.



# Version 0.1 (Public Experimental Snapshot - 1st Release | March 2, 2025)


- First release
