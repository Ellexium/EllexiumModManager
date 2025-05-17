-- Get the player's current vehicle object
local playerVehicle = be:getPlayerVehicle(0)

-- Check if the player vehicle exists to avoid errors
if playerVehicle then
  local playerVehicleID = playerVehicle:getID()
  local vehiclesToDelete = {} -- Create a new table to store vehicle objects to be deleted

  -- First pass: Iterate through all active vehicles and identify non-player vehicles.
  -- Add the vehicle objects themselves to our temporary list.
  for _, vehicleObject in activeVehiclesIterator() do
    if vehicleObject:getID() ~= playerVehicleID then
      table.insert(vehiclesToDelete, vehicleObject)
    end
  end

  -- Second pass: Iterate through our temporary list of vehicles to delete.
  -- Now it's safer to delete them as we are not iterating using the game's main vehicle iterator.
  for _, vehicleObjectToDelete in ipairs(vehiclesToDelete) do
    -- Add a check to ensure the vehicle object still exists and has a delete method
    -- This is a good practice, though often not strictly necessary if no other scripts are interfering.
    if vehicleObjectToDelete and type(vehicleObjectToDelete.delete) == 'function' then
      vehicleObjectToDelete:delete()
    else
      print("RemoveNonPlayerVehicles", "Attempted to delete an invalid or already deleted vehicle object.")
    end
  end

  if #vehiclesToDelete > 0 then
    print("RemoveNonPlayerVehicles", "Successfully processed " .. #vehiclesToDelete .. " non-player vehicle(s) for deletion.")
  else
    print("RemoveNonPlayerVehicles", "No non-player vehicles found to delete.")
  end

else
  print("RemoveNonPlayerVehicles", "Player vehicle not found. No vehicles were deleted.")
end