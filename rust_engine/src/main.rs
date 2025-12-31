use std::env;
use std::collections::HashMap;
use reqwest::header;
use serde::Deserialize;
use anyhow::Result;
use chrono::{NaiveDate, Datelike};

#[derive(Deserialize, Debug)]
struct TickerEntry {
    cik_str: u64,
    ticker: String,
}

#[derive(Deserialize, Debug)]
struct CompanyFacts {
    entityName: String,
    facts: FactsContainer,
}

#[derive(Deserialize, Debug)]
struct FactsContainer {
    #[serde(rename = "us-gaap")]
    us_gaap: Option<HashMap<String, FactData>>,
}

#[derive(Deserialize, Debug)]
struct FactData {
    units: HashMap<String, Vec<FactUnit>>,
}

#[derive(Deserialize, Debug)]
struct FactUnit {
    val: Option<f64>,
    fy: Option<u16>,
    fp: Option<String>,
    start: Option<String>,
    end: Option<String>,
}

const USER_AGENT: &str = "ValueDashboard contact@example.com"; 

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 { return Ok(()); }
    let target_ticker = args[1].to_uppercase();

    let client = reqwest::blocking::Client::builder()
        .user_agent(USER_AGENT)
        .build()?;

    // 1. Mapping
    let url_mapping = "https://www.sec.gov/files/company_tickers.json";
    let mapping_resp: HashMap<String, TickerEntry> = client.get(url_mapping).send()?.json()?;

    let mut target_cik = 0;
    for (_, entry) in mapping_resp {
        if entry.ticker == target_ticker {
            target_cik = entry.cik_str;
            break;
        }
    }

    if target_cik == 0 { return Ok(()); }
    let cik_padded = format!("{:0>10}", target_cik);
    
    // 2. Fetch Facts
    let url_facts = format!("https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json", cik_padded);
    let facts: CompanyFacts = client.get(&url_facts).send()?.json()?;

    // 3. Config Complète
    let metrics_config = vec![
        // --- FLUX (On vérifie la durée ~1 an) ---
        ("Revenue", vec!["Revenues", "SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueGoodsNet"], false),
        ("Net Income", vec!["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"], false),
        ("Operating Income (EBIT)", vec!["OperatingIncomeLoss"], false),
        ("EPS Diluted", vec!["EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted"], false),
        ("Operating Cash Flow", vec!["NetCashProvidedByUsedInOperatingActivities"], false),
        ("CapEx", vec!["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"], false),
        ("SBC", vec!["ShareBasedCompensation", "EmployeeServiceShareBasedCompensationNonvestedAwardsTotalCompensationCostNotYetRecognized", "ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsVestedInPeriodTotalFairValue"], false),
        
        // --- STOCKS (On prend le snapshot de fin d'année) ---
        ("Total Equity", vec!["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"], true),
        ("Cash & Equiv.", vec!["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsAndShortTermInvestments"], true),
        ("Long Term Debt", vec!["LongTermDebt", "LongTermDebtNoncurrent"], true),
        ("Shares Outstanding", vec!["CommonStockSharesOutstanding", "WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasicAndDiluted"], true),
    ];

    let mut results: HashMap<String, Vec<(u16, f64)>> = HashMap::new();

    if let Some(gaap) = facts.facts.us_gaap {
        for (metric_name, tags, is_instant) in metrics_config {
            let mut extracted_data = Vec::new();
            
            for tag in tags {
                if let Some(data) = gaap.get(tag) {
                    // On parcourt TOUTES les unités (USD, shares, etc.) sans distinction
                    for (_unit_name, units) in &data.units {
                        for unit in units {
                            if let Some(val) = unit.val {
                                // CONDITION SINE QUA NON : Avoir une date de fin
                                if let Some(end_s) = &unit.end {
                                    if let Ok(d_end) = NaiveDate::parse_from_str(end_s, "%Y-%m-%d") {
                                        
                                        // CAS 1 : FLUX (Revenue, OCF, SBC...)
                                        if !is_instant {
                                            // Il faut une date de début pour calculer la durée
                                            if let Some(start_s) = &unit.start {
                                                if let Ok(d_start) = NaiveDate::parse_from_str(start_s, "%Y-%m-%d") {
                                                    let duration_days = (d_end - d_start).num_days();
                                                    // On garde si c'est une année complète (350-380 jours)
                                                    if duration_days > 350 && duration_days < 380 {
                                                        let year = d_end.year() as u16;
                                                        extracted_data.push((year, val));
                                                    }
                                                }
                                            }
                                        } 
                                        // CAS 2 : STOCKS (Shares, Debt, Equity...)
                                        else {
                                            // On prend tout ce qui a une date. 
                                            // La logique de dédoublonnage (Max Absolu) plus bas fera le tri entre Q1, Q2, Q3 et FY.
                                            // Généralement, le chiffre de fin d'année (FY) est le plus élevé ou le plus significatif.
                                            // C'est un pari statistique qui marche à 99% pour éviter de perdre des données mal taguées.
                                            let year = d_end.year() as u16;
                                            extracted_data.push((year, val));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            // Dédoublonnage : On garde la valeur MAX absolue pour chaque année
            // Cela permet d'éliminer les valeurs trimestrielles (souvent plus petites) qui auraient pu passer
            // pour les métriques de Stock.
            let mut unique_map: HashMap<u16, f64> = HashMap::new();
            for (fy, val) in extracted_data {
                let entry = unique_map.entry(fy).or_insert(val);
                if val.abs() > entry.abs() {
                    *entry = val;
                }
            }
            
            let mut final_vec: Vec<(u16, f64)> = unique_map.into_iter().collect();
            final_vec.sort_by_key(|k| k.0);

            results.insert(metric_name.to_string(), final_vec);
        }
    }

    println!("{}", serde_json::json!({
        "ticker": target_ticker,
        "cik": target_cik,
        "name": facts.entityName,
        "financials": results
    }));

    Ok(())
}