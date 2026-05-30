package com.nutanix.tco;

import org.apache.poi.hssf.usermodel.*;
import org.apache.poi.ss.usermodel.*;
import javax.net.ssl.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.security.cert.X509Certificate;

/**
 * TCO Excel File Modifier using Apache POI (Java 8 compatible)
 * Apache POI preserves Excel file structure much better than Python libraries
 */
public class TcoModifier {
    
    // API Configuration
    private static final String API_URL = "https://ncm.services.nconprem-10-53-60-173.ccpnx.com/v1/cg/config/tco/purchases";
    private static final String USERNAME = "admin";
    private static final String PASSWORD = "Nutanix.123";
    
    // Download Configuration
    private static final int MAX_DOWNLOADS = 10000;  // Number of times to download and process
    private static final int DOWNLOADS_PER_MINUTE = 2;  // Rate limit for downloads
    private static final int SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE = 60;  // Seconds to sleep after rate limit
    private static final int RATE_LIMIT_SLEEP = 60;  // Seconds to sleep on 429 error
    
    // Modification Configuration
    private static final int ROWS_TO_MODIFY = 2500;  // Number of rows to modify per file
    private static final double CHANGE_AMOUNT = 1.0;  // Amount to add/subtract from cost values
    
    static {
        // Disable SSL verification (for testing only)
        try {
            TrustManager[] trustAllCerts = new TrustManager[]{
                new X509TrustManager() {
                    public X509Certificate[] getAcceptedIssuers() { return null; }
                    public void checkClientTrusted(X509Certificate[] certs, String authType) {}
                    public void checkServerTrusted(X509Certificate[] certs, String authType) {}
                }
            };
            SSLContext sc = SSLContext.getInstance("SSL");
            sc.init(null, trustAllCerts, new java.security.SecureRandom());
            HttpsURLConnection.setDefaultSSLSocketFactory(sc.getSocketFactory());
            HttpsURLConnection.setDefaultHostnameVerifier(new HostnameVerifier() {
                public boolean verify(String hostname, SSLSession session) { return true; }
            });
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    public static void main(String[] args) {
        long startTime = System.currentTimeMillis();
        int downloadCount = 0;
        int savedCount = 0;
        int failedCount = 0;
        int sleepCount = 0;
        
        try {
            printLine();
            System.out.println("TCO Modification Tool (Java + Apache POI)");
            System.out.println("Max Downloads: " + MAX_DOWNLOADS);
            System.out.println("Rate Limit: " + DOWNLOADS_PER_MINUTE + " downloads per minute");
            System.out.println("Rows to Modify: " + ROWS_TO_MODIFY);
            printLine();
            
            while (downloadCount < MAX_DOWNLOADS) {
                // Rate limiting: sleep after every DOWNLOADS_PER_MINUTE downloads
                if (downloadCount % DOWNLOADS_PER_MINUTE == 0 && downloadCount > 0) {
                    System.out.println("\nRate Limit: Sleeping for " + SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE + 
                        " seconds after " + DOWNLOADS_PER_MINUTE + " downloads...");
                    Thread.sleep(SLEEP_AFTER_EVERY_DOWNLOADS_PER_MINUTE * 1000);
                }
                
                System.out.println("\n--- Download & Process [" + (downloadCount + 1) + "/" + MAX_DOWNLOADS + "] ---");
                
                try {
                    // Step 1: Download TCO file
                    System.out.println("Step 1: Downloading TCO file...");
                    String downloadedFile = downloadTcoFile();
                    System.out.println("✓ Downloaded: " + downloadedFile);
                    
                    // Step 2: Modify the file
                    System.out.println("\nStep 2: Modifying Cost per Metering Unit values...");
                    String modifiedFile = modifyTcoFile(downloadedFile);
                    System.out.println("✓ Modified: " + modifiedFile);
                    
                    // Step 3: Upload modified file
                    System.out.println("\nStep 3: Uploading modified file...");
                    System.out.println("  Waiting 10 seconds to avoid rate limiting...");
                    Thread.sleep(10000);
                    
                    String response = uploadTcoFile(modifiedFile);
                    System.out.println("✓ Upload successful!");
                    System.out.println("  Response preview: " + 
                        (response.length() > 200 ? response.substring(0, 200) + "..." : response));
                    
                    downloadCount++;
                    savedCount++;
                    sleepCount = 0;  // Reset sleep count on success
                    
                    // Small delay between iterations
                    Thread.sleep(500);
                    
                } catch (Exception e) {
                    String errorMsg = e.getMessage();
                    
                    // Check if it's a rate limit error (429)
                    if (errorMsg != null && errorMsg.contains("429")) {
                        sleepCount++;
                        System.err.println("WARN: Rate limited (429). Sleeping for " + RATE_LIMIT_SLEEP + 
                            "s. Sleep count: " + sleepCount);
                        Thread.sleep(RATE_LIMIT_SLEEP * 1000);
                        // Don't increment downloadCount, retry this iteration
                        continue;
                    } else {
                        System.err.println("ERROR: " + errorMsg);
                        failedCount++;
                        downloadCount++;  // Count as attempted
                    }
                }
            }
            
            // Final statistics
            long endTime = System.currentTimeMillis();
            double duration = (endTime - startTime) / 1000.0;
            
            System.out.println("\n");
            printLine();
            System.out.println("FINAL STATISTICS");
            printLine();
            System.out.println("Total Downloads Attempted: " + downloadCount);
            System.out.println("Successfully Saved: " + savedCount);
            System.out.println("Failed: " + failedCount);
            System.out.println("Rate Limited Count: " + sleepCount);
            System.out.println("Duration: " + String.format("%.2f", duration) + " seconds");
            printLine();
            System.out.println("Files saved to: tco_reports/");
            printLine();
            
        } catch (Exception e) {
            System.err.println("FATAL ERROR: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    private static void printLine() {
        for (int i = 0; i < 80; i++) System.out.print("=");
        System.out.println();
    }
    
    /**
     * Download TCO file from API
     */
    private static String downloadTcoFile() throws Exception {
        URL url = new URL(API_URL);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        String auth = USERNAME + ":" + PASSWORD;
        String encodedAuth = Base64.getEncoder().encodeToString(auth.getBytes());
        conn.setRequestProperty("Authorization", "Basic " + encodedAuth);
        conn.setRequestMethod("GET");
        
        int responseCode = conn.getResponseCode();
        if (responseCode != 200) {
            throw new RuntimeException("Download failed: " + responseCode);
        }
        
        // Read response
        InputStream is = conn.getInputStream();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        int bytesRead;
        while ((bytesRead = is.read(buffer)) != -1) {
            baos.write(buffer, 0, bytesRead);
        }
        is.close();
        
        // Save to file
        String filename = "tco_reports/tco_downloaded_" + System.currentTimeMillis() + ".xls";
        new File("tco_reports").mkdirs();
        FileOutputStream fos = new FileOutputStream(filename);
        fos.write(baos.toByteArray());
        fos.close();
        
        return filename;
    }
    
    /**
     * Modify TCO file - only changes Cost per Metering Unit for custom costs
     */
    private static String modifyTcoFile(String inputFile) throws Exception {
        FileInputStream fis = new FileInputStream(inputFile);
        HSSFWorkbook workbook = new HSSFWorkbook(fis);
        fis.close();
        
        HSSFSheet sheet = workbook.getSheet("Direct_Costs");
        if (sheet == null) {
            throw new RuntimeException("Direct_Costs sheet not found");
        }
        
        // Get header row
        Row headerRow = sheet.getRow(0);
        int costColIdx = -1;
        int productNameColIdx = -1;
        int costTypeColIdx = -1;
        
        for (int i = 0; i < headerRow.getLastCellNum(); i++) {
            Cell cell = headerRow.getCell(i);
            if (cell != null) {
                String header = cell.getStringCellValue();
                if ("Cost per Metering Unit".equals(header)) {
                    costColIdx = i;
                } else if ("Product Name".equals(header)) {
                    productNameColIdx = i;
                } else if ("Cost Type".equals(header)) {
                    costTypeColIdx = i;
                }
            }
        }
        
        if (costColIdx == -1 || productNameColIdx == -1) {
            throw new RuntimeException("Required columns not found");
        }
        
        System.out.println("  Total rows: " + sheet.getLastRowNum());
        
        // Find custom cost rows
        List<Integer> customCostRows = new ArrayList<Integer>();
        for (int rowIdx = 1; rowIdx <= sheet.getLastRowNum(); rowIdx++) {
            Row row = sheet.getRow(rowIdx);
            if (row == null) continue;
            
            Cell productNameCell = row.getCell(productNameColIdx);
            Cell costCell = row.getCell(costColIdx);
            Cell costTypeCell = row.getCell(costTypeColIdx);
            
            if (productNameCell != null && costCell != null && costTypeCell != null) {
                String productName = getCellValueAsString(productNameCell);
                double costValue = getCellValueAsDouble(costCell);
                String costType = getCellValueAsString(costTypeCell);
                
                if (productName.startsWith("test_tco_config_") && 
                    costValue > 0 && 
                    !costType.isEmpty()) {
                    customCostRows.add(rowIdx);
                }
            }
        }
        
        System.out.println("  Custom cost rows found: " + customCostRows.size());
        
        // Select random rows
        Collections.shuffle(customCostRows);
        int numToModify = Math.min(ROWS_TO_MODIFY, customCostRows.size());
        List<Integer> rowsToModify = customCostRows.subList(0, numToModify);
        
        System.out.println("  Modifying " + numToModify + " random rows:");
        
        Random random = new Random();
        int modifiedCount = 0;
        
        for (Integer rowIdx : rowsToModify) {
            Row row = sheet.getRow(rowIdx);
            Cell costCell = row.getCell(costColIdx);
            Cell productNameCell = row.getCell(productNameColIdx);
            
            double currentValue = getCellValueAsDouble(costCell);
            String productName = getCellValueAsString(productNameCell);
            
            // Randomly add or subtract CHANGE_AMOUNT
            double change = random.nextBoolean() ? CHANGE_AMOUNT : -CHANGE_AMOUNT;
            double newValue = currentValue + change;
            
            // Ensure positive value
            if (newValue <= 0) {
                newValue = currentValue + Math.abs(change);
            }
            
            costCell.setCellValue(newValue);
            
            System.out.println("    Row " + (rowIdx + 1) + " (" + productName + "): " + 
                currentValue + " -> " + newValue);
            modifiedCount++;
        }
        
        System.out.println("  ✓ Modified " + modifiedCount + " rows");
        
        // Save
        String outputFile = inputFile.replace(".xls", "_modified.xls");
        FileOutputStream fos = new FileOutputStream(outputFile);
        workbook.write(fos);
        fos.close();
        workbook.close();
        
        return outputFile;
    }
    
    /**
     * Upload modified file to API
     */
    private static String uploadTcoFile(String filename) throws Exception {
        String boundary = "----WebKitFormBoundary" + System.currentTimeMillis();
        String LINE_FEED = "\r\n";
        
        URL url = new URL(API_URL);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        
        String auth = USERNAME + ":" + PASSWORD;
        String encodedAuth = Base64.getEncoder().encodeToString(auth.getBytes());
        conn.setRequestProperty("Authorization", "Basic " + encodedAuth);
        conn.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);
        
        OutputStream os = conn.getOutputStream();
        PrintWriter writer = new PrintWriter(new OutputStreamWriter(os, "UTF-8"), true);
        
        // Add file part
        writer.append("--" + boundary).append(LINE_FEED);
        writer.append("Content-Disposition: form-data; name=\"file\"; filename=\"" + 
            new File(filename).getName() + "\"").append(LINE_FEED);
        writer.append("Content-Type: application/vnd.ms-excel").append(LINE_FEED);
        writer.append(LINE_FEED).flush();
        
        FileInputStream fis = new FileInputStream(filename);
        byte[] buffer = new byte[4096];
        int bytesRead;
        while ((bytesRead = fis.read(buffer)) != -1) {
            os.write(buffer, 0, bytesRead);
        }
        os.flush();
        fis.close();
        
        writer.append(LINE_FEED).flush();
        writer.append("--" + boundary + "--").append(LINE_FEED).flush();
        writer.close();
        
        int responseCode = conn.getResponseCode();
        
        BufferedReader br;
        if (responseCode >= 400) {
            br = new BufferedReader(new InputStreamReader(conn.getErrorStream()));
        } else {
            br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        }
        
        StringBuilder response = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) {
            response.append(line);
        }
        br.close();
        
        if (responseCode >= 400) {
            throw new RuntimeException("Upload failed (" + responseCode + "): " + response.toString());
        }
        
        return response.toString();
    }
    
    private static String getCellValueAsString(Cell cell) {
        if (cell == null) return "";
        
        int cellType = cell.getCellType();
        if (cellType == Cell.CELL_TYPE_STRING) {
            return cell.getStringCellValue();
        } else if (cellType == Cell.CELL_TYPE_NUMERIC) {
            return String.valueOf(cell.getNumericCellValue());
        } else if (cellType == Cell.CELL_TYPE_BOOLEAN) {
            return String.valueOf(cell.getBooleanCellValue());
        } else if (cellType == Cell.CELL_TYPE_FORMULA) {
            return cell.getCellFormula();
        }
        return "";
    }
    
    private static double getCellValueAsDouble(Cell cell) {
        if (cell == null) return 0.0;
        
        int cellType = cell.getCellType();
        if (cellType == Cell.CELL_TYPE_NUMERIC) {
            return cell.getNumericCellValue();
        } else if (cellType == Cell.CELL_TYPE_STRING) {
            try {
                return Double.parseDouble(cell.getStringCellValue());
            } catch (NumberFormatException e) {
                return 0.0;
            }
        }
        return 0.0;
    }
}
