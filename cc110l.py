"""Defs pulled straight from CC110L datasheet.

Could also incorporate default values/Anarem-defined certification
validity/other metadata if needed. See:
http://www.anaren.com/sites/default/files/uploads/File/BoosterPack_Users_Manual.pdf
"""
from bitfield.spec import Region
# I want to define a state representation of the registers.
# I want to define two representations. One with only valid values... And one
# with invalid ones thrown in.
# High level state representation should be a bijection on binary encoding.
enum = lambda s:s.split()

# any 'magic' settings should come from smartrf studio
GDOx_CFG = ([
    'rx_fifo_full', 'rx_fifo_full_not_empty',
    'tx_fifo_full', 'tx_fifo_full_not_empty',
    'rx_fifo_overflow_not_flushed', 'tx_fifo_underflow_not_flushed',
    'packet_rx_tx_in_progress', 'good_crc_received', 'reserved',
    'channel_is_clear', 'pll_locked',
    'sync_serial_clock', 'sync_serial_data_out', 'async_serial_data_out',
    'carrier_sense', 'crc_ok'
] + ['reserved'] * 10)
GDOx_CFG += ([
    'PA_PD', 'LNA_PD',
] + ['reserved'] * 9 + [
    'clk_32k', 'reserved',
    'CHIP_RDYn', 'reserved',
    'XOSC_STABLE', 'reserved', 'reserved',
    'high_impedance',
    'ext_lna_or_pa_ctl',
] + ['CLK_XOSC_div_{0}'.format(n) for n 
    in [1, '1_5', 2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192]]
)
GDOx_INV = ['active_low', 'active_high'],

# gpio pins, sync word
r = Region(0x00, 0x06, '''
IOCFG2                 1:gdo2_invert 6:gdo2_cfg
IOCFG1 1:gdo_drive_str 1:gdo1_invert 6:gdo1_cfg
IOCFG0                 1:gdo0_invert 6:gdo0_cfg
FIFOTHR 1:adc_reten 2:close_in_rx 4:fifo_thresh
SYNC1: 8:sync_msb
SYNC0: 8:sync_lsb
''', mode='rw', bit_e='little', byte_e='little', bit_align=8, enums={
    'gdo2_invert': GDOx_INV, 'gdo1_invert': GDOx_INV, 'gdo0_invert': GDOx_INV, 
    'gdo2_cfg': GDOx_CFG, 'gdo1_cfg': GDOx_CFG, 'gdo0_cfg': GDOx_CFG,
    'close_in_rx':['0dB', '6dB', '12dB', '18dB'],
    'fifo_thresh':['4rx 61tx', '8rx 57tx', '12rx 53tx', '16rx 49tx', 
        '20rx 45tx', '24rx 41tx', '28rx 37tx', '32rx 33tx', '36rx 29tx', 
        '40rx 25tx', '44rx 21tx', '48rx 17tx', '52rx 13tx', '56rx 9tx', 
        '60rx 5tx', '64rx 1tx'],
})

# packet and frequency setup
r += Region(0x06, 0x10, '''
PKTLEN 8:pkt_len
PKTCTRL1 1:crc_autoflush 1:append_status 2:addr_check
PKTCTRL0 2:pkt_format 1:crc_enable 2:pkt_len_cfg
DEVICE_ADDR 8:device_addr
CHAN 8:chan_number
FSCTRL1 1:magic 5: freq_if
FREQOFF 8:freq_offset
FREQ2 8:freq_high
FREQ1 8:freq_mid
FREQ0 8:freq_low
''', enums={
    'addr_check':enum('none no_bcast bcast_00 bcast_00_ff'),
    'pkt_format':enum('normal sync_serial random_tx async_serial'),
    'pkt_len_cfg':enum('fixed var_1st_byte infinite reserved'),
})

# modem
r += Region(0x10, 0x16, '''
MDMCFG4 2:chanbw_exp 2:chanbw_mant  4:drate_exp
MDMCFG3 8:drate_mant
MDMCFG2 1:dem_dcfilt_off 3:mod_format 1:manchester_en 3:sync_mode
MDMCFG1 3:num_preamble 2:unused 2:chanspace_exp
MDMCFG0 8:chanspace_mant
DEVIATN 3:deviation_exp 1:unused 3:deviation_mant
''', enums={
    'mod_format':enum('fsk2 gfsk reserved ook fsk4' + ' reserved'*3),
    'sync_mode':enum('''
        no_preamble 
        on15of16 on16of16 on30of32
        carrier_sense
        cs_and_on15of16 cs_and_on16of16 cs_and_on30of32
    '''),
})

# main radio fsm, freq offset compensation, bit synchronization
r += Region(0x16, 0x1b, '''
MCSM2 1:rx_time_rssi 4:magic
MCSM1 2:cca_mode 2:rxoff_mode 2:txoff_mode
MCSM0 2:fs_autocal 2:po_timeout 1:magic 1:xosc_force_on
FOCCFG 1:foc_bs_cs_gate 2:force_pre_k 1:foc_post_k 2:foc_limit
BSCCFG 2:bs_pre_ki 2:bs_pre_kp 1:bs_post_ki 1:bs_post_kp 2:bs_limit
''', enums={
    'cca_mode':enum('always rssi not_rxing not_rxing_rssi'),
    'rxoff_mode':enum('idle fstxon tx stay_in_rx'),
    'txoff_mode':enum('idle fstxon stay_in_tx rx'),
    'fs_autocal':enum('never idle_to_rxtx rxtx_to_idle every_4th_idle'),
    'po_timeout':enum('1 16 64 256'),
})

# auto gain compensation, frontend lna, freq synth
r += Region(0x1b, 0x29, '''
AGCCTRL2 2:max_dvga_gain 3:max_lna_gain 3:magn_target
AGCCTRL1 1:agc_lna_priority 2:carrier_sense_rel_thr 4:carrier_sense_abs_thr
AGCCTRL0 2:hyst_level 2:wait_time 2:agc_freeze 2:filter_lengths
UNDOC_0x1E magic
UNDOC_0x1F magic
RESERVED3 5:magic 1:unused 2:magic
FREND1 2:lna_current 2:lna2mix_current 2:lodiv_buf_current_rx 2:mix_current
FREND0 2:lodiv_buf_current_tx 1:unused 3:pa_power
FSCAL3 2:fscal3_msb 2:chp_curr_cal_en 4:fscal3_lsb
FSCAL2 1:vco_core_h_en 5:fscal2
FSCAL1 6:fscal1
FSCAL0 7:fscal0
UNDOC_0x27 8:magic
UNDOC_0x28 8:magic
''', enums={
    'agc_freeze':enum('never frozen_during_rx manual_ana_only manual_both'),
})

# config registers that lose programming in SLEEP
# test registers that are SmartRF studio magic
r += Region(0x29, 0x30, '''
RESERVED2 8:magic
RESERVED1 8:magic
RESERVED0 8:magic
TEST2 8:test2
TEST1 8:test1
TEST0 6:test0_msb 1:vco_sel_cal_en 1:test0_lsb
UNDOC_0x2f 8:magic
''')

# READONLY status registers, including main radio control state
# accessible at 0x80 | addr?
r += Region(0x30, 0x3a, '''
PARTNUM 8:chip_part_no
VERSION 8:chip_vsn_no
FREQEST 8:freqoff_est
CRC_REG 1:crc_ok 7:reserved
RSSI 8:rssi
MARCSTATE 5:marc_state
PKTSTATUS 1:last_crc_ok 1:carrier_sense 1:reserved 1:chan_clear
          1:start_of_frame 1:gdo2_val 1:unused 1:gdo0_val
UNDOC_0x39 8:magic
TXBYTES 1:txfifo_underflow 7:num_txbytes
RXBYTES 1:rxfifo_underflow 7:num_rxbytes
''')
