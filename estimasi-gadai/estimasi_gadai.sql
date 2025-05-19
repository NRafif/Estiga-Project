-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 08, 2025 at 08:22 AM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.0.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `estimasi_gadai`
--

-- --------------------------------------------------------

--
-- Table structure for table `data_barang_referensi`
--

CREATE TABLE `data_barang_referensi` (
  `id` int(11) NOT NULL,
  `merk` varchar(100) NOT NULL,
  `tipe` varchar(100) NOT NULL,
  `ram` int(11) NOT NULL,
  `penyimpanan` int(11) NOT NULL,
  `tahun_rilis` int(11) NOT NULL,
  `harga_pasar` float NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `data_historis_hp`
--

CREATE TABLE `data_historis_hp` (
  `id` int(11) NOT NULL,
  `merk_hp` varchar(50) NOT NULL,
  `tipe_hp` varchar(50) NOT NULL,
  `ram` int(11) NOT NULL,
  `penyimpanan` int(11) NOT NULL,
  `tahun_keluaran` int(11) NOT NULL,
  `nilai_gadai` float NOT NULL,
  `tanggal_transaksi` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `estimasi`
--

CREATE TABLE `estimasi` (
  `id` int(11) NOT NULL,
  `nama_pemohon` varchar(100) NOT NULL,
  `merk_hp` varchar(50) NOT NULL,
  `tipe_hp` varchar(50) NOT NULL,
  `ram` int(11) NOT NULL,
  `penyimpanan` int(11) NOT NULL,
  `tahun_keluaran` int(11) NOT NULL,
  `harga_beli` float NOT NULL,
  `kondisi` varchar(10) NOT NULL,
  `estimasi_pinjaman` float NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `tanggal_pengajuan` datetime DEFAULT NULL,
  `tanggal_persetujuan` datetime DEFAULT NULL,
  `catatan_admin` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `gadai`
--

CREATE TABLE `gadai` (
  `id` int(11) NOT NULL,
  `nama_pemohon` varchar(100) NOT NULL,
  `merk_hp` varchar(50) NOT NULL,
  `tipe_hp` varchar(50) NOT NULL,
  `ram` int(11) NOT NULL,
  `penyimpanan` int(11) NOT NULL,
  `tahun_keluaran` int(11) NOT NULL,
  `harga_beli` float NOT NULL,
  `kondisi` varchar(50) NOT NULL,
  `tanggal_gadai` datetime DEFAULT NULL,
  `estimasi_pinjaman` float NOT NULL,
  `estimasi_minimum` float DEFAULT NULL,
  `estimasi_maximum` float DEFAULT NULL,
  `is_from_history` tinyint(1) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  `status` varchar(20) NOT NULL,
  `nilai_setelah_verifikasi` float DEFAULT NULL,
  `catatan_verifikasi` text DEFAULT NULL,
  `tanggal_verifikasi` datetime DEFAULT NULL,
  `verifikator_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `id` int(11) NOT NULL,
  `username` varchar(80) NOT NULL,
  `password` varchar(256) NOT NULL,
  `nama_lengkap` varchar(100) NOT NULL,
  `role` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`id`, `username`, `password`, `nama_lengkap`, `role`) VALUES
(2, 'Nofal', 'scrypt:32768:8:1$iFPiJtLBxvr9wzAD$830ad673801f76a6159891fd78faeb7b620ab69646871fa1875c216efc797ebe63a7ca2228251f6edb091f97596d12d8b3d07a9478c6710af21633051f76460b', 'Nofal Rafif', 'user'),
(3, 'admin', 'scrypt:32768:8:1$jMEaHwx4QVJdZyBq$70a751072c9f0d96c5716ca2bbca87a734b8c87258cea203e7bd16549a4896087244132385b0a3b7e45fc858e218aca0d5032778777ff29fd83a6281ce4e5d39', 'Administrator', 'admin');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `data_barang_referensi`
--
ALTER TABLE `data_barang_referensi`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `data_historis_hp`
--
ALTER TABLE `data_historis_hp`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `estimasi`
--
ALTER TABLE `estimasi`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `gadai`
--
ALTER TABLE `gadai`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `verifikator_id` (`verifikator_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `data_barang_referensi`
--
ALTER TABLE `data_barang_referensi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `data_historis_hp`
--
ALTER TABLE `data_historis_hp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `estimasi`
--
ALTER TABLE `estimasi`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `gadai`
--
ALTER TABLE `gadai`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `gadai`
--
ALTER TABLE `gadai`
  ADD CONSTRAINT `gadai_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  ADD CONSTRAINT `gadai_ibfk_2` FOREIGN KEY (`verifikator_id`) REFERENCES `user` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
