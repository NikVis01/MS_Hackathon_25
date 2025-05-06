
/**
 * Converts a timestamp string to a formatted time string
 */
export const formatTimeString = (timestamp: string): string => {
  // If it's already in HH:MM:SS format, return as is
  if (/^\d{2}:\d{2}:\d{2}$/.test(timestamp)) {
    return timestamp;
  }
  
  // If it's a date string or timestamp, format it
  try {
    const date = new Date(timestamp);
    return date.toTimeString().split(' ')[0];
  } catch (e) {
    console.error("Invalid timestamp format:", timestamp);
    return timestamp; // Return original if parsing fails
  }
};

/**
 * Calculates a time offset from a base time
 * @param baseTime - Base time in format HH:MM:SS
 * @param offsetSeconds - Seconds to offset (positive or negative)
 */
export const calculateTimeOffset = (baseTime: string, offsetSeconds: number): string => {
  const [hours, minutes, seconds] = baseTime.split(':').map(Number);
  
  let totalSeconds = hours * 3600 + minutes * 60 + seconds + offsetSeconds;
  
  // Handle negative times by wrapping to previous day
  if (totalSeconds < 0) {
    totalSeconds = 86400 + totalSeconds; // 24 * 60 * 60 = 86400 seconds in a day
  }
  
  // Handle overflow to next day
  totalSeconds = totalSeconds % 86400;
  
  const newHours = Math.floor(totalSeconds / 3600);
  const newMinutes = Math.floor((totalSeconds % 3600) / 60);
  const newSeconds = totalSeconds % 60;
  
  return [newHours, newMinutes, newSeconds]
    .map(unit => unit.toString().padStart(2, '0'))
    .join(':');
};

/**
 * Formats a URL with timestamp parameters
 * @param baseUrl - Base video URL
 * @param startTime - Start time in format HH:MM:SS
 * @param eventTime - Event time in format HH:MM:SS
 */
export const formatVideoUrlWithTimestamp = (baseUrl: string, startTime: string, eventTime: string): string => {
  // This function needs to be adapted based on your video server's API
  // This is just an example format
  try {
    const url = new URL(baseUrl);
    url.searchParams.append('start', startTime.replace(/:/g, ''));
    url.searchParams.append('event', eventTime.replace(/:/g, ''));
    return url.toString();
  } catch (e) {
    // If URL parsing fails, just append parameters
    const separator = baseUrl.includes('?') ? '&' : '?';
    return `${baseUrl}${separator}start=${startTime.replace(/:/g, '')}&event=${eventTime.replace(/:/g, '')}`;
  }
};
